import { useState } from "react";
import { Calendar, Clock, MapPin, Loader2, Users, X, Ban, Star } from "lucide-react";
import { ApiError, formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useBookingDetail, useCancelBooking, useCreateReview, useGroupDetail } from "./hooks/useBookings";
import { ConfirmModal } from "../../components/ConfirmModal/ConfirmModal";
import { StarRow } from "../../components/StarRow/StarRow";
import styles from "./BookingDetailModal.module.scss";

interface BookingDetailModalProps {
    bookingId: number | null;
    onClose: () => void;
}

const CANCELABLE_STATUSES = new Set(["PENDING", "CONFIRMED"]);

const CANCEL_ERROR_MESSAGE: Record<string, string> = {
    INVALID_STATE: "Essa reserva não pode mais ser cancelada.",
    RESOURCE_NOT_OWNED: "Você não pode cancelar essa reserva.",
};

const REVIEW_ERROR_MESSAGE: Record<string, string> = {
    ALREADY_REVIEWED: "Você já avaliou essa reserva.",
    BOOKING_NOT_ELIGIBLE_FOR_REVIEW: "Essa reserva não está elegível para avaliação.",
};

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
    const cancelBooking = useCancelBooking();
    const [confirmingCancel, setConfirmingCancel] = useState(false);

    const createReview = useCreateReview();
    const [reviewRating, setReviewRating] = useState(0);
    const [reviewComment, setReviewComment] = useState("");
    const [reviewSent, setReviewSent] = useState(false);

    if (!bookingId) return null;

    function handleCancel() {
        if (!bookingId) return;
        cancelBooking.mutate(bookingId, { onSuccess: () => setConfirmingCancel(false) });
    }

    function handleSubmitReview() {
        if (!bookingId || reviewRating === 0) return;
        createReview.mutate(
            { bookingId, rating: reviewRating, comment: reviewComment.trim() || null },
            { onSuccess: () => setReviewSent(true) }
        );
    }

    const cancelError = cancelBooking.error as ApiError | undefined;
    const friendlyCancelError = cancelError
        ? (cancelError.code && CANCEL_ERROR_MESSAGE[cancelError.code]) || cancelError.message
        : null;

    const reviewError = createReview.error as ApiError | undefined;
    const friendlyReviewError = reviewError
        ? (reviewError.code && REVIEW_ERROR_MESSAGE[reviewError.code]) || reviewError.message
        : null;
    const alreadyReviewed = reviewError?.code === "ALREADY_REVIEWED";

    return (
        <>
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

                        {booking.status === "COMPLETED" && (
                            <div className={styles["review-card"]}>
                                {reviewSent || alreadyReviewed ? (
                                    <p className={styles["review-thanks"]}>
                                        {alreadyReviewed ? "Você já avaliou essa reserva." : "Obrigado pela avaliação!"}
                                    </p>
                                ) : (
                                    <>
                                        <h3 className={styles["review-title"]}>Como foi sua partida?</h3>
                                        <StarRow rating={reviewRating} size="md" onRate={setReviewRating} />
                                        <label htmlFor="review-comment" className={styles["review-label"]}>
                                            Comentário (opcional)
                                        </label>
                                        <textarea
                                            id="review-comment"
                                            className={styles["review-textarea"]}
                                            value={reviewComment}
                                            onChange={(e) => setReviewComment(e.target.value)}
                                            placeholder="Conte como foi a experiência na quadra..."
                                            maxLength={2000}
                                        />
                                        {friendlyReviewError && !alreadyReviewed && (
                                            <p className={styles["error"]} role="alert">{friendlyReviewError}</p>
                                        )}
                                        <button
                                            onClick={handleSubmitReview}
                                            disabled={reviewRating === 0 || createReview.isPending}
                                            className={styles["review-submit"]}
                                        >
                                            <Star width={15} height={15} />
                                            {createReview.isPending ? "Enviando..." : "Enviar avaliação"}
                                        </button>
                                    </>
                                )}
                            </div>
                        )}

                        {friendlyCancelError && <p className={styles["error"]}>{friendlyCancelError}</p>}

                        {CANCELABLE_STATUSES.has(booking.status) && (
                            <button
                                onClick={() => setConfirmingCancel(true)}
                                disabled={cancelBooking.isPending}
                                className={styles["cancel-btn"]}
                            >
                                {cancelBooking.isPending ? "Cancelando..." : "Cancelar reserva"}
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>

        <ConfirmModal
            open={confirmingCancel}
            icon={<Ban width={22} height={22} />}
            title="Cancelar reserva?"
            message="Essa ação não pode ser desfeita. Se você cancelar dentro do prazo de reembolso, o valor pago será estornado."
            confirmLabel="Cancelar reserva"
            cancelLabel="Voltar"
            danger
            onConfirm={handleCancel}
            onCancel={() => setConfirmingCancel(false)}
        />
        </>
    );
}

export default BookingDetailModal;
