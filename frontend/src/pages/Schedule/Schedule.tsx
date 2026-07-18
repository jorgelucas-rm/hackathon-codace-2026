import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, MapPin, Calendar, Clock, Shield, Users, CheckCircle, Sunrise, Sun, Moon, Trophy, Timer, Loader2, Minus, Plus, Repeat } from "lucide-react";
import { Screen } from "../../types";
import { AvailabilitySlot, formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useAvailability, useCompanyDetail, useCourt, useCreateBooking, useCreateGroupBooking } from "./hooks/useSchedule";
import styles from "./Schedule.module.scss";

const MIN_GROUP_SPOTS = 2;

interface ScheduleProps {
    courtId: number | null;
    onNavigate: (screen: Screen) => void;
    onBookingCreated: (paymentId: number) => void;
}

const PERIODS = {
    manha: { Icon: Sunrise, label: "Manhã" },
    tarde: { Icon: Sun, label: "Tarde" },
    noite: { Icon: Moon, label: "Noite" },
};

function periodOf(startTime: string): keyof typeof PERIODS {
    const hour = Number(startTime.slice(0, 2));
    if (hour < 12) return "manha";
    if (hour < 18) return "tarde";
    return "noite";
}

function buildDays(count: number) {
    const days: { label: string; date: string; iso: string }[] = [];
    const today = new Date();
    for (let i = 0; i < count; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        const label = i === 0 ? "Hoje" : i === 1 ? "Amanhã" : d.toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
        days.push({
            label: label.charAt(0).toUpperCase() + label.slice(1),
            date: String(d.getDate()),
            iso: d.toISOString().slice(0, 10),
        });
    }
    return days;
}

export function Schedule({ courtId, onNavigate, onBookingCreated }: ScheduleProps) {
    const navigate = useNavigate();
    const days = useMemo(() => buildDays(7), []);
    const [selectedDay, setSelectedDay] = useState(0);
    const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
    const [reservationType, setReservationType] = useState<"private" | "group">("private");
    const [groupSpots, setGroupSpots] = useState(MIN_GROUP_SPOTS);
    const [bookingError, setBookingError] = useState<string | null>(null);

    const selectedDate = days[selectedDay].iso;

    const { data: court, isLoading: courtLoading } = useCourt(courtId);
    const { data: company } = useCompanyDetail(court?.company.id ?? 0);
    const { data: availability, isLoading: availabilityLoading, isError: availabilityError } = useAvailability(courtId, selectedDate);
    const createBooking = useCreateBooking();
    const createGroupBooking = useCreateGroupBooking();

    const siblingCourts = (company?.courts ?? []).filter((c) => c.status === "ACTIVE");
    const maxGroupSpots = Math.max(MIN_GROUP_SPOTS, court?.capacity ?? MIN_GROUP_SPOTS);

    // Sempre que a quadra muda (ou a capacidade fica menor que o valor
    // escolhido), reancora o seletor de vagas num valor válido.
    useEffect(() => {
        setGroupSpots((prev) => Math.min(Math.max(prev, MIN_GROUP_SPOTS), maxGroupSpots));
    }, [maxGroupSpots]);

    function handleSwitchCourt(newCourtId: number) {
        if (newCourtId === courtId) return;
        setSelectedSlot(null);
        setBookingError(null);
        navigate(`/schedule/${newCourtId}`);
    }

    const slotsByPeriod: Record<keyof typeof PERIODS, AvailabilitySlot[]> = { manha: [], tarde: [], noite: [] };
    for (const slot of availability?.slots ?? []) {
        slotsByPeriod[periodOf(slot.start_time)].push(slot);
    }

    const total = selectedSlot ? formatPriceCents(selectedSlot.price) : "—";
    const spotPrice = selectedSlot ? formatPriceCents(Math.ceil(selectedSlot.price / groupSpots)) : "—";
    const price = reservationType === "group" ? spotPrice : total;

    const slotClass = (slot: AvailabilitySlot, isSelected: boolean) => {
        if (isSelected) return styles["slot-selected"];
        if (slot.status !== "free") return styles["slot-busy"];
        return styles["slot-free"];
    };

    const reservationTypes = [
        { key: "private" as const, Icon: Shield, title: "Privada", desc: "Você e seus amigos" },
        { key: "group" as const, Icon: Users, title: "Grupo aberto", desc: "Divida o custo" },
    ];

    function handleSelectSlot(slot: AvailabilitySlot) {
        if (slot.status !== "free") return;
        setBookingError(null);
        setSelectedSlot((prev) => (prev?.start_time === slot.start_time ? null : slot));
    }

    // Prazo de fechamento do grupo: 2h antes do jogo, sem nunca cair antes de
    // "agora" nem depois do início da partida (regra validada no backend).
    function computeClosingDeadline(date: string, startTime: string): string {
        // O backend interpreta `date`+`start_time` como UTC
        // (`datetime.combine(..., tzinfo=timezone.utc)` em group_service.py) —
        // por isso o "Z" aqui, para não introduzir um offset pelo fuso local
        // do navegador e acabar mandando um closing_deadline depois do
        // game_start que o backend calcula (o que rejeita com 422/INVALID_GROUP_CONFIG).
        const gameStart = new Date(`${date}T${startTime}Z`);
        const twoHoursBefore = new Date(gameStart.getTime() - 2 * 60 * 60 * 1000);
        const soon = new Date(Date.now() + 15 * 60 * 1000);
        const deadline = twoHoursBefore.getTime() > soon.getTime() ? twoHoursBefore : soon;
        return (deadline.getTime() < gameStart.getTime() ? deadline : new Date(gameStart.getTime() - 5 * 60 * 1000)).toISOString();
    }

    function handleContinue() {
        if (!selectedSlot || !courtId) return;
        setBookingError(null);

        if (reservationType === "group") {
            createGroupBooking.mutate(
                {
                    courtId,
                    date: selectedDate,
                    startTime: selectedSlot.start_time,
                    endTime: selectedSlot.end_time,
                    group: {
                        totalSpots: groupSpots,
                        minSpots: Math.min(MIN_GROUP_SPOTS, groupSpots),
                        visibility: "public",
                        closingDeadline: computeClosingDeadline(selectedDate, selectedSlot.start_time),
                        leftoverRule: "creator_absorbs",
                    },
                },
                {
                    onSuccess: (result) => onBookingCreated(result.payment.id),
                    onError: (err) => setBookingError(err.message),
                }
            );
            return;
        }

        createBooking.mutate(
            {
                courtId,
                date: selectedDate,
                startTime: selectedSlot.start_time,
                endTime: selectedSlot.end_time,
            },
            {
                onSuccess: (result) => onBookingCreated(result.payment.id),
                onError: (err) => setBookingError(err.message),
            }
        );
    }

    const isSubmitting = createBooking.isPending || createGroupBooking.isPending;
    const canContinue = !!selectedSlot && !!courtId
        && (reservationType === "private" || (reservationType === "group" && groupSpots >= MIN_GROUP_SPOTS))
        && !isSubmitting;

    if (!courtId) {
        return (
            <div className={styles["container"]}>
                <div className={styles["content"]} style={{ padding: "64px 0", textAlign: "center" }}>
                    <p>Nenhuma quadra selecionada. Volte e escolha uma arena/quadra primeiro.</p>
                    <button onClick={() => onNavigate("courts")}>Ver arenas</button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles["container"]}>
            <div className={styles["main"]}>
                {/* ---------- Header compacto ---------- */}
                <header className={styles["header"]}>
                    <button onClick={() => onNavigate("courtDetail")} className={styles["back"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <div>
                        <span className={styles["eyebrow"]}>Reservar</span>
                        <h1>Escolher horário</h1>
                    </div>
                </header>

                <div className={styles["content"]}>
                    {/* ---------- Resumo da quadra (compacto) ---------- */}
                    <div className={styles["court-summary"]}>
                        <div className={styles["court-thumb"]} style={{ background: "linear-gradient(135deg, rgba(173,153,0,0.2), #E8D7BD)" }}>
                            <Trophy width={22} height={22} />
                        </div>
                        <div className={styles["court-info"]}>
                            <p className={styles["court-name"]}>{court?.name ?? (courtLoading ? "Carregando..." : "Quadra")}</p>
                            <p className={styles["court-place"]}><MapPin width={12} height={12} /> {court ? `${court.company.city}, ${court.company.state}` : "—"}</p>
                            <span className={styles["court-sport"]}>{court?.sports.map((s) => s.name).join(", ") ?? "—"}</span>
                        </div>
                        <div className={styles["court-price"]}>
                            <span className={styles["eyebrow"]}>Por hora</span>
                            <strong>{formatPriceCents(court?.base_price_hour)}</strong>
                        </div>
                    </div>

                    {/* ---------- Trocar quadra (mesma arena) ---------- */}
                    {siblingCourts.length > 1 && (
                        <section className={styles["block"]}>
                            <p className={styles["block-label"]}><Repeat width={14} height={14} /> Trocar de quadra</p>
                            <div className={`scrollbar-none ${styles["courts-switch"]}`}>
                                {siblingCourts.map((c) => (
                                    <button
                                        key={c.id}
                                        onClick={() => handleSwitchCourt(c.id)}
                                        className={`${styles["court-chip"]} ${c.id === courtId ? styles["court-chip-active"] : ""}`}
                                    >
                                        <strong>{c.name}</strong>
                                        <span>{formatPriceCents(c.base_price_hour)}/h</span>
                                    </button>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* ---------- Data ---------- */}
                    <section className={styles["block"]}>
                        <p className={styles["block-label"]}>Escolha o dia</p>
                        <div className={`scrollbar-none ${styles["days"]}`}>
                            {days.map((day, i) => (
                                <button
                                    key={i}
                                    onClick={() => { setSelectedDay(i); setSelectedSlot(null); }}
                                    className={`${styles["day"]} ${selectedDay === i ? styles["day-active"] : ""}`}
                                >
                                    <span>{day.label}</span>
                                    <strong>{day.date}</strong>
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* ---------- Tipo de reserva ---------- */}
                    <section className={styles["block"]}>
                        <p className={styles["block-label"]}>Tipo de reserva</p>
                        <div className={styles["types"]}>
                            {reservationTypes.map((opt) => (
                                <button
                                    key={opt.key}
                                    onClick={() => setReservationType(opt.key)}
                                    className={`${styles["type"]} ${reservationType === opt.key ? styles["type-active"] : ""}`}
                                >
                                    <opt.Icon width={18} height={18} />
                                    <span className={styles["type-title"]}>{opt.title}</span>
                                    <span className={styles["type-desc"]}>{opt.desc}</span>
                                </button>
                            ))}
                        </div>
                        {reservationType === "group" && (
                            <div className={styles["group-config"]}>
                                <p className={styles["group-config-label"]}>Quantas vagas o grupo vai ter?</p>
                                <div className={styles["spots-stepper"]}>
                                    <button
                                        type="button"
                                        onClick={() => setGroupSpots((n) => Math.max(MIN_GROUP_SPOTS, n - 1))}
                                        disabled={groupSpots <= MIN_GROUP_SPOTS}
                                        className={styles["spot-btn"]}
                                        aria-label="Diminuir vagas"
                                    >
                                        <Minus width={16} height={16} />
                                    </button>
                                    <div className={styles["spot-value"]}>
                                        <strong>{groupSpots}</strong>
                                        <span>vagas</span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setGroupSpots((n) => Math.min(maxGroupSpots, n + 1))}
                                        disabled={groupSpots >= maxGroupSpots}
                                        className={styles["spot-btn"]}
                                        aria-label="Aumentar vagas"
                                    >
                                        <Plus width={16} height={16} />
                                    </button>
                                </div>
                                <p className={styles["group-config-hint"]}>
                                    Máximo de {maxGroupSpots} vagas (capacidade da quadra). Cada pessoa paga {spotPrice}.
                                </p>
                            </div>
                        )}
                    </section>

                    {/* ---------- Horários ---------- */}
                    {availabilityLoading && (
                        <div className={styles["block"]} style={{ textAlign: "center", padding: "24px 0" }}>
                            <Loader2 width={28} height={28} />
                            <p>Carregando horários...</p>
                        </div>
                    )}

                    {availabilityError && !availabilityLoading && (
                        <div className={styles["block"]} style={{ textAlign: "center", padding: "24px 0" }}>
                            <p>Não foi possível carregar os horários desse dia.</p>
                        </div>
                    )}

                    {!availabilityLoading && !availabilityError && (availability?.slots.length ?? 0) === 0 && (
                        <div className={styles["block"]} style={{ textAlign: "center", padding: "24px 0" }}>
                            <p>Essa quadra não abre nesse dia.</p>
                        </div>
                    )}

                    {(["manha", "tarde", "noite"] as const).map((period) => {
                        if (slotsByPeriod[period].length === 0) return null;
                        const PeriodIcon = PERIODS[period].Icon;
                        return (
                            <section key={period} className={styles["block"]}>
                                <p className={styles["block-label"]}><PeriodIcon width={14} height={14} /> {PERIODS[period].label}</p>
                                <div className={styles["slots"]}>
                                    {slotsByPeriod[period].map((slot) => {
                                        const isSelected = selectedSlot?.start_time === slot.start_time;
                                        const disabled = slot.status !== "free";
                                        return (
                                            <button
                                                key={slot.start_time}
                                                onClick={() => handleSelectSlot(slot)}
                                                disabled={disabled}
                                                className={`${styles["slot"]} ${slotClass(slot, isSelected)}`}
                                            >
                                                <div className={styles["slot-head"]}>
                                                    <strong>{formatHHMM(slot.start_time)}</strong>
                                                    {isSelected && <CheckCircle width={16} height={16} />}
                                                </div>
                                                <span className={styles["slot-price"]}>{formatPriceCents(slot.price)}</span>
                                                {slot.status === "open_group" && !isSelected && <em className={styles["tag-last"]}>Grupo aberto</em>}
                                                {slot.status === "busy" && <em className={styles["tag-busy"]}>Reservado</em>}
                                            </button>
                                        );
                                    })}
                                </div>
                            </section>
                        );
                    })}

                    {bookingError && (
                        <div className={styles["block"]}>
                            <p style={{ color: "crimson" }}>{bookingError}</p>
                        </div>
                    )}

                    <div className={styles["spacer"]} />
                </div>
            </div>

            {/* ---------- Resumo lateral (desktop) ---------- */}
            <aside className={styles["summary"]}>
                <div className={styles["summary-head"]}>
                    <span className={styles["eyebrow"]}>Resumo</span>
                    <h2>Sua reserva</h2>
                </div>
                <div className={styles["summary-body"]}>
                    <div className={styles["summary-row"]}><span><Trophy width={15} height={15} /> Quadra</span><strong>{court?.name ?? "—"}</strong></div>
                    <div className={styles["summary-row"]}><span><Calendar width={15} height={15} /> Data</span><strong>{days[selectedDay].label}, {days[selectedDay].date}</strong></div>
                    <div className={styles["summary-row"]}><span><Clock width={15} height={15} /> Horário</span><strong>{selectedSlot ? formatHHMM(selectedSlot.start_time) : "—"}</strong></div>
                    <div className={styles["summary-row"]}><span><Timer width={15} height={15} /> Duração</span><strong>{selectedSlot ? "1h" : "—"}</strong></div>
                    {reservationType === "group" && (
                        <div className={styles["summary-row"]}><span><Users width={15} height={15} /> Vagas</span><strong>{groupSpots}</strong></div>
                    )}

                    <div className={styles["summary-divider"]} />

                    <div className={styles["summary-line"]}><span>{reservationType === "group" ? "Valor total do horário" : "Valor"}</span><span>{total}</span></div>
                    <div className={styles["summary-total"]}>
                        <span>{reservationType === "group" ? "Sua cota agora" : "Total"}</span>
                        <strong>{price}</strong>
                    </div>
                </div>
                <div className={styles["summary-foot"]}>
                    <button onClick={handleContinue} disabled={!canContinue} className={styles["cta"]}>
                        {isSubmitting ? "Enviando..." : !selectedSlot ? "Selecione um horário" : reservationType === "group" ? "Criar grupo aberto" : "Continuar reserva"}
                    </button>
                </div>
            </aside>

            {/* ---------- Barra fixa (mobile) ---------- */}
            <div className={styles["mobile-bar"]}>
                <div className={styles["mobile-info"]}>
                    <span className={styles["mobile-label"]}>{selectedSlot ? `${days[selectedDay].label} · ${formatHHMM(selectedSlot.start_time)}` : "Nenhum horário"}</span>
                    <strong className={styles["mobile-total"]}>{price}</strong>
                </div>
                <button onClick={handleContinue} disabled={!canContinue} className={styles["cta"]}>
                    {isSubmitting ? "Enviando..." : !selectedSlot ? "Escolher horário" : reservationType === "group" ? "Criar grupo" : "Continuar"}
                </button>
            </div>
        </div>
    );
}

export default Schedule;
