import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, CheckCircle, CreditCard, CircleDot, Lock, Loader2 } from "lucide-react";
import { Screen } from "../../types";
import { formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useCourt } from "../../hooks/useCourt";
import { useBookingByPayment, useConfirmPayment, usePayment } from "./hooks/useCheckout";
import styles from "./Checkout.module.scss";

interface CheckoutProps {
    paymentId: number | null;
    onNavigate: (screen: Screen) => void;
}

export function Checkout({ paymentId, onNavigate }: CheckoutProps) {
    const [method, setMethod] = useState<"PIX" | "CARD">("PIX");
    const [error, setError] = useState<string | null>(null);
    const queryClient = useQueryClient();

    const { data: payment, isLoading: paymentLoading } = usePayment(paymentId);
    const isBooking = payment?.reference_type === "booking";
    const { data: booking } = useBookingByPayment(isBooking ? payment?.reference_id : undefined);
    const { data: court } = useCourt(booking?.court_id);
    const confirmPayment = useConfirmPayment();

    if (!paymentId) {
        return (
            <div className={styles["container"]}>
                <div className={styles["header"]}>
                    <button onClick={() => onNavigate("home")} className={styles["back"]}>
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <h1>Checkout / Pagamento</h1>
                </div>
                <div className={styles["body"]}>
                    <p>Nenhuma reserva selecionada. Volte e escolha um horário primeiro.</p>
                </div>
            </div>
        );
    }

    if (paymentLoading || !payment) {
        return (
            <div className={styles["container"]}>
                <div className={styles["body"]} style={{ textAlign: "center", padding: "64px 0" }}>
                    <Loader2 width={36} height={36} />
                    <p>Carregando sua reserva...</p>
                </div>
            </div>
        );
    }

    if (payment.status === "APPROVED") {
        return (
            <div className={styles["success"]}>
                <div className={styles["success-icon"]}>
                    <CheckCircle width={48} height={48} />
                </div>
                <h1>Reserva Confirmada!</h1>
                <p>
                    {court && booking
                        ? `Sua reserva na ${court.name} em ${booking.date} às ${formatHHMM(booking.start_time)} foi confirmada com sucesso.`
                        : "Sua reserva foi confirmada com sucesso."}
                </p>
                <button onClick={() => onNavigate("home")} className="button-primary">
                    Voltar para o início
                </button>
            </div>
        );
    }

    if (payment.status !== "PENDING") {
        return (
            <div className={styles["success"]}>
                <h1>Pagamento {payment.status === "DENIED" ? "recusado" : payment.status.toLowerCase()}</h1>
                <p>Esse pagamento já foi processado e não está mais pendente.</p>
                <button onClick={() => onNavigate("home")} className="button-primary">
                    Voltar para o início
                </button>
            </div>
        );
    }

    const paymentOptions = [
        { key: "PIX" as const, className: styles["pay-pix"], label: "Pix", sub: "Pagamento instantâneo", node: <span>Pix</span> },
        { key: "CARD" as const, className: styles["pay-credit"], label: "Cartão de Crédito", sub: "simulado — sem cobrança real", node: <CreditCard width={20} height={20} /> },
    ];

    function handleConfirm() {
        if (!paymentId) return;
        setError(null);
        confirmPayment.mutate(
            { paymentId, method },
            {
                onSuccess: (updatedPayment) => {
                    // `confirm` também muda o status do booking em cadeia
                    // (efeito no backend) — sem isso, o resumo continuaria
                    // mostrando o payment como PENDING (cache antigo do
                    // react-query) mesmo já aprovado no servidor.
                    queryClient.setQueryData(["payment", paymentId], updatedPayment);
                    if (booking) {
                        queryClient.invalidateQueries({ queryKey: ["booking", booking.id] });
                    }
                },
                onError: (err) => setError(err.message),
            }
        );
    }

    return (
        <div className={styles["container"]}>
            <div className={styles["header"]}>
                <button onClick={() => onNavigate("schedule")} className={styles["back"]}>
                    <ChevronLeft width={20} height={20} />
                </button>
                <h1>Checkout / Pagamento</h1>
            </div>

            <div className={styles["body"]}>
                <div className={`surface-card ${styles["card"]}`}>
                    <h2>Resumo da Reserva</h2>
                    <div className={styles["summary-court"]}>
                        <div className={styles["court-emoji"]}><CircleDot width={24} height={24} /></div>
                        <div>
                            <p className={styles["court-name"]}>{court ? `${court.company.name} · ${court.name}` : "Carregando..."}</p>
                            {court && <p>{court.company.city}, {court.company.state}</p>}
                            {booking && <p>{booking.date} · {formatHHMM(booking.start_time)} – {formatHHMM(booking.end_time)}</p>}
                        </div>
                    </div>
                    <div className={styles["lines"]}>
                        <div className={styles["total"]}>
                            <span>Total a Pagar</span>
                            <strong>{formatPriceCents(payment.amount)}</strong>
                        </div>
                    </div>
                </div>

                <div className={`surface-card ${styles["card"]}`}>
                    <h2>Método de Pagamento</h2>
                    <p style={{ fontSize: 13, opacity: 0.7 }}>Simulador de gateway — nenhum pagamento real é processado.</p>
                    <div className={styles["payments"]}>
                        {paymentOptions.map((opt) => (
                            <button
                                key={opt.key}
                                onClick={() => setMethod(opt.key)}
                                className={`${styles["payment"]} ${method === opt.key ? styles["payment-active"] : ""}`}
                            >
                                <div className={`${styles["pay-icon"]} ${opt.className}`}>{opt.node}</div>
                                <div className={styles["pay-info"]}>
                                    <p>{opt.label}</p>
                                    <span>{opt.sub}</span>
                                </div>
                                <div className={styles["radio"]}>
                                    {method === opt.key && <span />}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {error && <p style={{ color: "crimson" }}>{error}</p>}

                <button
                    onClick={handleConfirm}
                    disabled={confirmPayment.isPending}
                    className={`button-primary ${styles["confirm"]}`}
                >
                    {confirmPayment.isPending ? "Confirmando..." : "Confirmar e Pagar"}
                </button>
                <p className={styles["secure"]}><Lock width={12} height={12} /> Pagamento 100% seguro e criptografado</p>
            </div>
        </div>
    );
}

export default Checkout;
