import { useMemo, useState } from "react";
import { Ban, Loader2, User } from "lucide-react";
import {
    PanelCourt,
    ScheduleBooking,
    formatHHMM,
    formatPriceCents,
} from "../../../services/companyPanel.service";
import {
    useCancelBookingByCompany,
    useCreateBlock,
    useCreateManualBooking,
    useMyCourts,
    useMySchedule,
    useRemoveBlock,
} from "../hooks/useCompanyPanel";
import { HOURS, dateLabel, isValidHHMM, next7Days, nextHour } from "../panelUtils";
import styles from "../CompanyPanel.module.scss";

// ---------------------------------------------------------------------------
// Estado dos modais da agenda
// ---------------------------------------------------------------------------

type AgendaModal =
    | { kind: "free"; court: PanelCourt; time: string }
    | { kind: "manual"; court: PanelCourt; time: string }
    | { kind: "block"; court: PanelCourt; time: string }
    | { kind: "detail"; booking: ScheduleBooking; courtName: string }
    | null;

type CellKind = "confirmed" | "pending" | "group" | "blocked";

const VISIBLE_STATUS = ["CONFIRMED", "PENDING", "BLOCKED"];

function cellKind(b: ScheduleBooking): CellKind {
    if (b.status === "BLOCKED") return "blocked";
    if (b.group) return "group";
    if (b.status === "PENDING") return "pending";
    return "confirmed";
}

const CELL_CLASS: Record<CellKind, string> = {
    confirmed: styles["cell-confirmed"],
    pending: styles["cell-pending"],
    group: styles["cell-group"],
    blocked: styles["cell-blocked"],
};

function cellName(b: ScheduleBooking): string {
    if (b.status === "BLOCKED") return "Bloqueado";
    return b.customer?.name || (b.group ? "Grupo aberto" : "Cliente");
}

function cellSub(b: ScheduleBooking): string {
    if (b.status === "BLOCKED") return b.reason || "sem motivo";
    if (b.group) return `${formatPriceCents(b.group.spot_price)}/vaga · fecha ${formatHHMM(b.start_time)}`;
    if (b.status === "PENDING") return `${formatPriceCents(b.total_price)} · aguardando pgto`;
    return formatPriceCents(b.total_price);
}

function cellBadge(b: ScheduleBooking): string | null {
    if (b.status === "BLOCKED") return null;
    if (b.group) return `Grupo ${b.group.filled_spots}/${b.group.total_spots}`;
    if (b.status === "PENDING") return "Pendente";
    return "Confirmada";
}

function bookingRevenue(b: ScheduleBooking): number {
    return b.group ? b.group.filled_spots * b.group.spot_price : b.total_price;
}

// ---------------------------------------------------------------------------
// Aba Agenda
// ---------------------------------------------------------------------------

export function AgendaTab() {
    const days = useMemo(() => next7Days(), []);
    const [dateIdx, setDateIdx] = useState(0);
    const [modal, setModal] = useState<AgendaModal>(null);

    const selectedDate = days[dateIdx].iso;
    const { data: schedule, isLoading: loadingSchedule, isError: errorSchedule } = useMySchedule(selectedDate);
    const { data: courts, isLoading: loadingCourts, isError: errorCourts } = useMyCourts();

    const activeCourts = useMemo(
        () => (courts ?? []).filter((c) => c.status === "ACTIVE"),
        [courts]
    );

    const bookingsByCourt = useMemo(() => {
        const map = new Map<number, ScheduleBooking[]>();
        (schedule?.courts ?? []).forEach((cs) => {
            map.set(cs.court_id, cs.bookings.filter((b) => VISIBLE_STATUS.includes(b.status)));
        });
        return map;
    }, [schedule]);

    const dayBookings = useMemo(() => {
        const all: ScheduleBooking[] = [];
        bookingsByCourt.forEach((list) => all.push(...list));
        return all;
    }, [bookingsByCourt]);

    const nRes = dayBookings.filter((b) => b.status !== "BLOCKED").length;
    const nBlq = dayBookings.filter((b) => b.status === "BLOCKED").length;
    const revenue = dayBookings
        .filter((b) => b.status === "CONFIRMED")
        .reduce((acc, b) => acc + bookingRevenue(b), 0);
    const summary = `${nRes} reservas · ${formatPriceCents(revenue)} confirmados · ${nBlq} bloqueio${nBlq === 1 ? "" : "s"}`;

    function findBooking(courtId: number, hour: string): ScheduleBooking | undefined {
        return (bookingsByCourt.get(courtId) ?? []).find(
            (b) => formatHHMM(b.start_time) <= hour && hour < formatHHMM(b.end_time)
        );
    }

    const isLoading = loadingSchedule || loadingCourts;
    const isError = errorSchedule || errorCourts;

    return (
        <>
            <div className={styles["tab-head"]}>
                <div>
                    <div className={styles["eyebrow"]}>Sua operação</div>
                    <div className={styles["tab-title"]}>Agenda do dia</div>
                </div>
                <div className={styles["summary"]}>{summary}</div>
            </div>

            <div className={styles["date-chips"]}>
                {days.map((d, i) => (
                    <button
                        key={d.iso}
                        onClick={() => setDateIdx(i)}
                        className={`${styles["date-chip"]} ${i === dateIdx ? styles["date-chip-active"] : ""}`}
                    >
                        <span>{d.week}</span>
                        <strong>{d.day}</strong>
                    </button>
                ))}
            </div>

            <div className={styles["legend"]}>
                <span><i className={`${styles["dot"]} ${styles["dot-confirmed"]}`} />Confirmada</span>
                <span><i className={`${styles["dot"]} ${styles["dot-pending"]}`} />Pendente</span>
                <span><i className={`${styles["dot"]} ${styles["dot-group"]}`} />Grupo aberto</span>
                <span><i className={`${styles["dot"]} ${styles["dot-blocked"]}`} />Bloqueado</span>
                <span><i className={`${styles["dot"]} ${styles["dot-free"]}`} />Livre — clique para bloquear ou reservar</span>
            </div>

            {isLoading && (
                <div className={styles["state-msg"]}><Loader2 width={18} height={18} /> Carregando agenda...</div>
            )}
            {isError && !isLoading && (
                <div className={`${styles["state-msg"]} ${styles["state-error"]}`}>Erro ao carregar a agenda. Tente novamente.</div>
            )}
            {!isLoading && !isError && activeCourts.length === 0 && (
                <div className={styles["state-msg"]}>
                    Nenhuma quadra ativa — cadastre uma quadra na aba Quadras para abrir a agenda.
                </div>
            )}

            {!isLoading && !isError && activeCourts.length > 0 && (
                <div className={styles["grid-card"]}>
                    <div className={styles["grid-inner"]}>
                        <div className={styles["grid-header"]}>
                            <div className={styles["time-col"]} />
                            <div className={styles["cols"]}>
                                {activeCourts.map((c) => (
                                    <div key={c.id} className={styles["col-head"]}>
                                        {c.name}
                                        <span>
                                            {c.sports.map((s) => s.name).join(" · ") || "—"} · {formatPriceCents(c.base_price_hour)}/h
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {HOURS.map((hour) => (
                            <div key={hour} className={styles["grid-row"]}>
                                <div className={styles["time-col"]}>{hour}</div>
                                <div className={styles["cols"]}>
                                    {activeCourts.map((court) => {
                                        const booking = findBooking(court.id, hour);
                                        return (
                                            <div key={court.id} className={styles["cell-wrap"]}>
                                                {booking ? (
                                                    <button
                                                        className={`${styles["cell-busy"]} ${CELL_CLASS[cellKind(booking)]}`}
                                                        onClick={() => setModal({ kind: "detail", booking, courtName: court.name })}
                                                    >
                                                        <div className={styles["cell-top"]}>
                                                            <span className={styles["cell-name"]}>{cellName(booking)}</span>
                                                            {cellBadge(booking) && (
                                                                <span className={styles["cell-badge"]}>{cellBadge(booking)}</span>
                                                            )}
                                                        </div>
                                                        <div className={styles["cell-sub"]}>{cellSub(booking)}</div>
                                                    </button>
                                                ) : (
                                                    <button
                                                        className={styles["cell-free"]}
                                                        onClick={() => setModal({ kind: "free", court, time: hour })}
                                                        aria-label={`Horário livre ${hour} — ${court.name}`}
                                                    >
                                                        +
                                                    </button>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {modal && (
                <AgendaModals
                    modal={modal}
                    date={selectedDate}
                    onChange={setModal}
                    onClose={() => setModal(null)}
                />
            )}
        </>
    );
}

// ---------------------------------------------------------------------------
// Modais: horário livre -> reserva manual | bloqueio; detalhe de reserva
// ---------------------------------------------------------------------------

function AgendaModals({
    modal,
    date,
    onChange,
    onClose,
}: {
    modal: NonNullable<AgendaModal>;
    date: string;
    onChange: (m: AgendaModal) => void;
    onClose: () => void;
}) {
    return (
        <div className={styles["modal-overlay"]} onClick={onClose} role="dialog" aria-modal="true">
            <div className={styles["modal"]} onClick={(e) => e.stopPropagation()}>
                {modal.kind === "free" && <FreeModal modal={modal} date={date} onChange={onChange} />}
                {modal.kind === "manual" && <ManualModal modal={modal} date={date} onClose={onClose} />}
                {modal.kind === "block" && <BlockModal modal={modal} date={date} onClose={onClose} />}
                {modal.kind === "detail" && <DetailModal modal={modal} date={date} onClose={onClose} />}
            </div>
        </div>
    );
}

function slotTitle(courtName: string, date: string, time: string): string {
    return `${courtName} · ${dateLabel(date)} · ${time}`;
}

function FreeModal({
    modal,
    date,
    onChange,
}: {
    modal: Extract<NonNullable<AgendaModal>, { kind: "free" }>;
    date: string;
    onChange: (m: AgendaModal) => void;
}) {
    return (
        <>
            <div className={styles["modal-eyebrow"]}>Horário livre</div>
            <div className={styles["modal-title"]}>{slotTitle(modal.court.name, date, modal.time)}</div>
            <div className={styles["option-list"]}>
                <button
                    className={styles["option-btn"]}
                    onClick={() => onChange({ kind: "manual", court: modal.court, time: modal.time })}
                >
                    <div className={`${styles["option-icon"]} ${styles["option-icon-teal"]}`}>
                        <User width={20} height={20} />
                    </div>
                    <div className={styles["option-text"]}>
                        <strong>Reserva manual (balcão)</strong>
                        <span>Cliente ligou ou apareceu no local — já nasce confirmada, sem pagamento pelo app.</span>
                    </div>
                </button>
                <button
                    className={styles["option-btn"]}
                    onClick={() => onChange({ kind: "block", court: modal.court, time: modal.time })}
                >
                    <div className={`${styles["option-icon"]} ${styles["option-icon-gray"]}`}>
                        <Ban width={20} height={20} />
                    </div>
                    <div className={styles["option-text"]}>
                        <strong>Bloquear horário</strong>
                        <span>Manutenção, evento privado — tira o horário de circulação.</span>
                    </div>
                </button>
            </div>
        </>
    );
}

function ManualModal({
    modal,
    date,
    onClose,
}: {
    modal: Extract<NonNullable<AgendaModal>, { kind: "manual" }>;
    date: string;
    onClose: () => void;
}) {
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [end, setEnd] = useState(nextHour(modal.time));
    const [error, setError] = useState("");
    const mutation = useCreateManualBooking();

    const submit = () => {
        if (!name.trim() || !phone.trim()) {
            setError("Informe o nome e o telefone do cliente.");
            return;
        }
        if (!isValidHHMM(end) || end <= modal.time) {
            setError("Horário de fim inválido — use HH:MM depois do início.");
            return;
        }
        setError("");
        mutation.mutate(
            {
                court_id: modal.court.id,
                date,
                start_time: modal.time,
                end_time: end,
                customer_name: name.trim(),
                customer_phone: phone.trim(),
            },
            { onSuccess: onClose, onError: (e: Error) => setError(e.message) }
        );
    };

    return (
        <>
            <div className={styles["modal-eyebrow"]}>Reserva manual</div>
            <div className={styles["modal-title"]}>{slotTitle(modal.court.name, date, modal.time)}</div>

            <label className={styles["field-label"]}>Nome do cliente</label>
            <input
                className={styles["modal-input"]}
                placeholder="ex.: João da Silva"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            <label className={`${styles["field-label"]} ${styles["field-gap"]}`}>Telefone</label>
            <input
                className={styles["modal-input"]}
                placeholder="(85) 9 8888-7777"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
            />

            <div className={styles["modal-row"]}>
                <div>
                    <label className={styles["field-label"]}>Início</label>
                    <input className={styles["modal-input"]} value={modal.time} readOnly />
                </div>
                <div>
                    <label className={styles["field-label"]}>Fim</label>
                    <input className={styles["modal-input"]} value={end} onChange={(e) => setEnd(e.target.value)} />
                </div>
            </div>

            <div className={styles["price-note"]}>
                <span>Valor registrado (pago fora do app)</span>
                <span>{formatPriceCents(modal.court.base_price_hour)}</span>
            </div>

            {error && <p className={styles["form-error"]}>{error}</p>}

            <button className={styles["modal-primary-btn"]} onClick={submit} disabled={mutation.isPending}>
                {mutation.isPending ? "Confirmando..." : "Confirmar reserva"}
            </button>
        </>
    );
}

function BlockModal({
    modal,
    date,
    onClose,
}: {
    modal: Extract<NonNullable<AgendaModal>, { kind: "block" }>;
    date: string;
    onClose: () => void;
}) {
    const [end, setEnd] = useState(nextHour(modal.time));
    const [reason, setReason] = useState("");
    const [error, setError] = useState("");
    const mutation = useCreateBlock();

    const submit = () => {
        if (!isValidHHMM(end) || end <= modal.time) {
            setError("Horário de fim inválido — use HH:MM depois do início.");
            return;
        }
        setError("");
        mutation.mutate(
            {
                courtId: modal.court.id,
                dto: {
                    date,
                    start_time: modal.time,
                    end_time: end,
                    reason: reason.trim() || undefined,
                },
            },
            { onSuccess: onClose, onError: (e: Error) => setError(e.message) }
        );
    };

    return (
        <>
            <div className={styles["modal-eyebrow"]}>Bloquear horário</div>
            <div className={styles["modal-title"]}>{slotTitle(modal.court.name, date, modal.time)}</div>

            <div className={styles["modal-row"]} style={{ marginTop: 0 }}>
                <div>
                    <label className={styles["field-label"]}>Início</label>
                    <input className={styles["modal-input"]} value={modal.time} readOnly />
                </div>
                <div>
                    <label className={styles["field-label"]}>Fim</label>
                    <input className={styles["modal-input"]} value={end} onChange={(e) => setEnd(e.target.value)} />
                </div>
            </div>

            <label className={`${styles["field-label"]} ${styles["field-gap"]}`}>Motivo (opcional)</label>
            <input
                className={styles["modal-input"]}
                placeholder="ex.: manutenção da rede"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
            />

            {error && <p className={styles["form-error"]}>{error}</p>}

            <button className={styles["block-btn"]} onClick={submit} disabled={mutation.isPending}>
                {mutation.isPending ? "Bloqueando..." : "Bloquear horário"}
            </button>
        </>
    );
}

function DetailModal({
    modal,
    date,
    onClose,
}: {
    modal: Extract<NonNullable<AgendaModal>, { kind: "detail" }>;
    date: string;
    onClose: () => void;
}) {
    const [error, setError] = useState("");
    const cancelMutation = useCancelBookingByCompany();
    const unblockMutation = useRemoveBlock();

    const b = modal.booking;
    const isBlock = b.status === "BLOCKED";
    const kind = cellKind(b);

    const kindLabel = isBlock
        ? "Bloqueio"
        : b.group
            ? "Reserva de grupo aberto"
            : "Reserva";
    const title = isBlock ? "Horário bloqueado" : cellName(b);
    const badge = cellBadge(b);

    const rows: { label: string; value: string }[] = [
        { label: "Quadra", value: modal.courtName },
        { label: "Horário", value: `${dateLabel(date)} · ${formatHHMM(b.start_time)} – ${formatHHMM(b.end_time)}` },
    ];
    if (isBlock) {
        rows.push({ label: "Motivo", value: b.reason || "—" });
    } else {
        if (b.customer?.phone) rows.push({ label: "Telefone", value: b.customer.phone });
        if (b.group) {
            rows.push({
                label: "Vagas",
                value: `${b.group.filled_spots} de ${b.group.total_spots} preenchidas (mín. ${b.group.min_spots})`,
            });
            rows.push({ label: "Valor por vaga", value: formatPriceCents(b.group.spot_price) });
            rows.push({ label: "Arrecadado", value: formatPriceCents(b.group.filled_spots * b.group.spot_price) });
        } else {
            rows.push({ label: "Valor", value: formatPriceCents(b.total_price) });
        }
    }

    const badgeStyle: Record<CellKind, { background: string; color: string }> = {
        confirmed: { background: "#c8ece4", color: "#0b7d6e" },
        pending: { background: "#f1e3ae", color: "#7a6414" },
        group: { background: "#e2dfae", color: "#6b6a10" },
        blocked: { background: "#eee6d6", color: "#8b8272" },
    };

    const pending = cancelMutation.isPending || unblockMutation.isPending;
    const options = { onSuccess: onClose, onError: (e: Error) => setError(e.message) };

    return (
        <>
            <div className={styles["modal-head"]}>
                <div>
                    <div className={styles["modal-eyebrow"]}>{kindLabel}</div>
                    <div className={styles["modal-title"]}>{title}</div>
                </div>
                {badge && (
                    <span className={styles["modal-badge"]} style={badgeStyle[kind]}>{badge}</span>
                )}
            </div>

            <div className={styles["detail-rows"]}>
                {rows.map((row) => (
                    <div key={row.label} className={styles["detail-row"]}>
                        <span>{row.label}</span>
                        <span>{row.value}</span>
                    </div>
                ))}
            </div>

            {b.group && (
                <div className={styles["group-note"]}>
                    Cancelar esta reserva cancela o grupo inteiro e estorna os {b.group.filled_spots} participantes
                    que já pagaram.
                </div>
            )}

            {error && <p className={styles["form-error"]}>{error}</p>}

            {isBlock ? (
                <button
                    className={styles["modal-primary-btn"]}
                    onClick={() => unblockMutation.mutate(b.id, options)}
                    disabled={pending}
                >
                    {pending ? "Desbloqueando..." : "Desbloquear horário"}
                </button>
            ) : (
                <button
                    className={styles["danger-btn"]}
                    onClick={() => cancelMutation.mutate(b.id, options)}
                    disabled={pending}
                >
                    {pending ? "Cancelando..." : "Cancelar reserva — estorno integral"}
                </button>
            )}
        </>
    );
}

export default AgendaTab;
