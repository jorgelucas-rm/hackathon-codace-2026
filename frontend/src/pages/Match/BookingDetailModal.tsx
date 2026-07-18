import { Calendar, Clock, MapPin, Loader2, Users, X } from "lucide-react";
import { formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useBookingDetail, useGroupDetail } from "./hooks/useBookings";
import styles from "./BookingDetailModal.module.scss";

interface BookingDetailModalProps {
    bookingId: number | null;
    onClose: () => void;
}

const STATUS_LABEL: Record<string, string> = {
    PENDING: "Pendente",
    CONFIRMED: "Confirmado",
    CANCELED: "Cancelado",
    COMPLETED: "Concluído",
    BLOCKED: "Bloqueado",
};

const STATUS_CLASS: Record<string, string> = {
    PENDING: "status-upcoming",
    CONFIRMED: "status-upcoming",
    COMPLETED: "status-done",
    CANCELED: "status-cancel",
    BLOCKED: "status-cancel",
};

function formatDate(date: string): string {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

function initials(name: string | null): string {
    if (!name) return "?";
    return name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((p) => p[0]?.toUpperCase())
        .join("");
}

const MEMBER_STATUS_LABEL: Record<string, string> = {
    PENDING: "Pendente",
    CONFIRMED: "Confirmado",
    CANCELED: "Saiu",
};

export function BookingDetailModal({ bookingId, onClose }: BookingDetailModalProps) {
    const { data: booking, isLoading, isError } = useBookingDetail(bookingId);
    const groupId = booking?.type === "GROUP" ? booking.group?.id ?? null : null;
    const { data: group, isLoading: groupLoading } = useGroupDetail(groupId);

    if (!bookingId) return null;

    return (
        <div className={styles["overlay"]} onClick={onClose} role="dialog" aria-modal="true">
            <div className={styles["modal"]} onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} className={styles["close"]} aria-label="Fechar">
                    <X width={18} height={18} />
                </button>

                {isLoading && (
                    <div className={styles["state"]}>
                        <Loader2 width={22} height={22} className={styles["spin"]} />
                        <span>Carregando reserva...</span>
                    </div>
                )}

                {isError && !isLoading && (
                    <div className={styles["state"]}>
                        <span>Não foi possível carregar essa reserva.</span>
                    </div>
                )}

                {booking && !isLoading && (
                    <>
                        <div className={styles["head"]}>
                            <span className={`${styles["status"]} ${styles[STATUS_CLASS[booking.status] ?? "status-upcoming"]}`}>
                                {STATUS_LABEL[booking.status] ?? booking.status}
                            </span>
                            {booking.type === "GROUP" && (
                                <span className={styles["type-chip"]}><Users width={13} height={13} /> Grupo aberto</span>
                            )}
                        </div>

                        <h2 className={styles["title"]}>{booking.court_name ?? "Reserva"}</h2>
                        {booking.company_name && <p className={styles["subtitle"]}>{booking.company_name}</p>}

                        {booking.sport_names.length > 0 && (
                            <div className={styles["sports"]}>
                                {booking.sport_names.map((s) => (
                                    <span key={s} className={styles["sport-chip"]}>{s}</span>
                                ))}
                            </div>
                        )}

                        <div className={styles["info-list"]}>
                            <div className={styles["info-row"]}>
                                <Calendar width={16} height={16} />
                                <span>{formatDate(booking.date)}</span>
                            </div>
                            <div className={styles["info-row"]}>
                                <Clock width={16} height={16} />
                                <span>{formatHHMM(booking.start_time)} – {formatHHMM(booking.end_time)}</span>
                            </div>
                            {booking.court_name && (
                                <div className={styles["info-row"]}>
                                    <MapPin width={16} height={16} />
                                    <span>{booking.court_name}</span>
                                </div>
                            )}
                        </div>

                        <div className={styles["price-row"]}>
                            <span>{booking.type === "GROUP" ? "Valor por jogador" : "Valor total"}</span>
                            <strong>{formatPriceCents(booking.type === "GROUP" ? booking.group?.spot_price ?? booking.total_price : booking.total_price)}</strong>
                        </div>

                        {booking.type === "GROUP" && booking.group && (
                            <div className={styles["group-card"]}>
                                <div className={styles["group-head"]}>
                                    <h3>Grupo</h3>
                                    <span className={styles["group-count"]}>
                                        {booking.group.filled_spots}<small>/{booking.group.total_spots}</small>
                                    </span>
                                </div>

                                <div className={styles["progress"]}>
                                    <div className={styles["bar"]}>
                                        <div
                                            className={styles["fill"]}
                                            style={{ width: `${Math.min(100, Math.round((booking.group.filled_spots / booking.group.total_spots) * 100))}%` }}
                                        />
                                    </div>
                                    <span className={styles["left"]}>
                                        {Math.max(0, booking.group.total_spots - booking.group.filled_spots)} vagas
                                    </span>
                                </div>

                                {groupLoading && (
                                    <div className={styles["state"]}>
                                        <Loader2 width={16} height={16} className={styles["spin"]} />
                                        <span>Carregando participantes...</span>
                                    </div>
                                )}

                                {group && group.members.length > 0 && (
                                    <ul className={styles["members"]}>
                                        {group.members.map((m) => (
                                            <li key={m.id} className={styles["member"]}>
                                                <span className={styles["member-avatar"]}>{initials(m.user_name)}</span>
                                                <span className={styles["member-name"]}>{m.user_name ?? `Usuário #${m.user_id}`}</span>
                                                <span className={styles["member-status"]}>{MEMBER_STATUS_LABEL[m.status] ?? m.status}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}

                                {group && group.members.length === 0 && !groupLoading && (
                                    <p className={styles["members-empty"]}>Nenhum participante confirmado ainda.</p>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default BookingDetailModal;
