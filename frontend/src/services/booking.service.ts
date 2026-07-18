// Service de agendamento (disponibilidade, criar reserva, pagamento) —
// integração real com o backend. Mesmo padrão de auth.service.ts/
// companies.service.ts (envelope { code, message, error_code, data, status }).
//
// Endpoints usados aqui:
//   GET  /api/courts/{id}                    -> detalhe público de uma quadra
//   GET  /api/courts/{id}/availability?date=  -> slots do dia (público)
//   POST /api/bookings                        -> cria reserva (auth USER)
//   GET  /api/bookings/{id}                   -> detalhe da reserva (auth)
//   GET  /api/payments/{id}                   -> detalhe do pagamento (auth USER)
//   POST /api/payments/{id}/confirm           -> simulador de gateway (auth USER)

import { getToken } from "./auth.service";
import { Sport } from "./companies.service";

export interface CourtCompanySummary {
    id: number;
    name: string;
    city: string;
    state: string;
    latitude: number | null;
    longitude: number | null;
}

export interface CourtDetail {
    id: number;
    company_id: number;
    name: string;
    capacity: number;
    photos: string[];
    base_price_hour: number;
    status: string;
    sports: Sport[];
    company: CourtCompanySummary;
}

export interface AvailabilityGroup {
    id: number;
    total_spots: number;
    filled_spots: number;
    spot_price: number;
    closing_deadline: string;
}

export interface AvailabilitySlot {
    start_time: string;
    end_time: string;
    status: "free" | "busy" | "open_group";
    price: number;
    group: AvailabilityGroup | null;
}

export interface AvailabilityResponse {
    court_id: number;
    date: string;
    slots: AvailabilitySlot[];
}

export type BookingStatus = "PENDING" | "CONFIRMED" | "CANCELED" | "COMPLETED" | "BLOCKED";
export type PaymentStatus = "PENDING" | "APPROVED" | "DENIED" | "REFUNDED";

export interface BookingRead {
    id: number;
    court_id: number;
    creator_user_id: number | null;
    creator_company_id: number | null;
    date: string;
    start_time: string;
    end_time: string;
    type: "CLOSED" | "GROUP";
    status: BookingStatus;
    reason: string | null;
    total_price: number;
    customer_name: string | null;
    customer_phone: string | null;
    created_at: string;
}

export interface PaymentSummary {
    id: number;
    reference_type: string;
    reference_id: number;
    amount: number;
    method: "PIX" | "CARD" | null;
    status: PaymentStatus;
    created_at: string;
}

export interface PaymentRead extends PaymentSummary {
    company_payout: number | null;
    platform_fee: number | null;
    gateway_fee: number | null;
    refunded_at: string | null;
}

export interface BookingCreateResponse {
    booking: BookingRead;
    payment: PaymentSummary;
}

interface Envelope<T> {
    code: number;
    message: string;
    error_code?: string | null;
    data: T;
}

function authHeaders(): Record<string, string> {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function getJson<T>(url: string, fallbackError: string, auth = false): Promise<Envelope<T>> {
    const res = await fetch(url, { headers: auth ? authHeaders() : {} });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.message || fallbackError);
    return json as Envelope<T>;
}

async function postJsonAuth<T>(url: string, body: unknown, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.message || fallbackError);
    return json as Envelope<T>;
}

export async function getCourt(courtId: number): Promise<CourtDetail> {
    const json = await getJson<CourtDetail>(`/api/courts/${courtId}`, "Erro ao buscar a quadra");
    return json.data;
}

export async function getAvailability(courtId: number, date: string): Promise<AvailabilityResponse> {
    const json = await getJson<AvailabilityResponse>(
        `/api/courts/${courtId}/availability?date=${date}`,
        "Erro ao buscar a disponibilidade"
    );
    return json.data;
}

export async function createClosedBooking(
    courtId: number,
    date: string,
    startTime: string,
    endTime: string
): Promise<BookingCreateResponse> {
    const json = await postJsonAuth<BookingCreateResponse>(
        "/api/bookings",
        { court_id: courtId, date, start_time: startTime, end_time: endTime, type: "closed" },
        "Erro ao criar a reserva"
    );
    return json.data;
}

export async function getBooking(bookingId: number): Promise<BookingRead> {
    const json = await getJson<BookingRead>(`/api/bookings/${bookingId}`, "Erro ao buscar a reserva", true);
    return json.data;
}

export async function getPayment(paymentId: number): Promise<PaymentRead> {
    const json = await getJson<PaymentRead>(`/api/payments/${paymentId}`, "Erro ao buscar o pagamento", true);
    return json.data;
}

export async function confirmPayment(
    paymentId: number,
    result: "approved" | "denied",
    method: "PIX" | "CARD"
): Promise<PaymentRead> {
    const json = await postJsonAuth<PaymentRead>(
        `/api/payments/${paymentId}/confirm`,
        { result, method },
        "Erro ao confirmar o pagamento"
    );
    return json.data;
}

export function formatPriceCents(cents: number | null | undefined): string {
    if (cents === null || cents === undefined) return "—";
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatHHMM(time: string): string {
    return time.slice(0, 5);
}
