import { useState } from "react";
import { Calendar, Clock, MapPin, Loader2, Users, X, Ban } from "lucide-react";
import { ApiError, formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useGroupDetail, useJoinGroup, useLeaveGroup } from "../../hooks/useGroups";
import { ConfirmModal } from "../ConfirmModal/ConfirmModal";
import styles from "./JoinGroupModal.module.scss";

interface JoinGroupModalProps {
    groupId: number | null;
    onClose: () => void;
    onJoined: (paymentId: number) => void;
    /** "manage": usuário já é membro — mostra "Sair do grupo" em vez de "Entrar". */
    mode?: "join" | "manage";
}

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

const JOIN_ERROR_MESSAGE: Record<string, string> = {
    ALREADY_MEMBER: "Você já faz parte desse grupo.",
    GROUP_FULL: "Esse grupo já está com todas as vagas preenchidas.",
    INVALID_STATE: "Esse grupo não está mais aberto para novos jogadores.",
};

const LEAVE_ERROR_MESSAGE: Record<string, string> = {
    NOT_GROUP_MEMBER: "Você não faz mais parte desse grupo.",
    INVALID_STATE: "Quem criou o grupo não pode sair — cancele a reserva.",
};

export function JoinGroupModal({ groupId, onClose, onJoined, mode = "join" }: JoinGroupModalProps) {
    const { data: group, isLoading, isError } = useGroupDetail(groupId);
    const join = useJoinGroup();
    const leave = useLeaveGroup();
    const [confirmingLeave, setConfirmingLeave] = useState(false);

    if (!groupId) return null;

    function handleJoin() {
        if (!groupId) return;
        join.mutate(groupId, {
            onSuccess: (res) => onJoined(res.payment.id),
        });
    }

    function handleLeave() {
        if (!groupId) return;
        leave.mutate(groupId, { onSuccess: () => { setConfirmingLeave(false); onClose(); } });
    }

    const spotsLeft = group ? Math.max(0, group.total_spots - group.filled_spots) : 0;
    const joinError = join.error as ApiError | undefined;
    const friendlyJoinError = joinError
        ? (joinError.code && JOIN_ERROR_MESSAGE[joinError.code]) || joinError.message
        : null;
    const leaveError = leave.error as ApiError | undefined;
    const friendlyLeaveError = leaveError
        ? (leaveError.code && LEAVE_ERROR_MESSAGE[leaveError.code]) || leaveError.message
        : null;
    const friendlyError = mode === "manage" ? friendlyLeaveError : friendlyJoinError;

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
                        <span>Carregando partida...</span>
                    </div>
                )}

                {isError && !isLoading && (
                    <div className={styles["state"]}>
                        <span>Não foi possível carregar essa partida.</span>
                    </div>
                )}

                {group && !isLoading && (
                    <>
                        <div className={styles["head"]}>
                            <span className={styles["open-badge"]}><i className={styles["dot"]} /> Grupo Aberto</span>
                        </div>

                        <h2 className={styles["title"]}>{group.court_name ?? "Partida aberta"}</h2>
                        {group.company_name && <p className={styles["subtitle"]}>{group.company_name}</p>}

                        <div className={styles["info-list"]}>
                            <div className={styles["info-row"]}>
                                <Calendar width={16} height={16} />
                                <span>{formatDate(group.date)}</span>
                            </div>
                            <div className={styles["info-row"]}>
                                <Clock width={16} height={16} />
                                <span>{formatHHMM(group.start_time)} – {formatHHMM(group.end_time)}</span>
                            </div>
                            {group.court_name && (
                                <div className={styles["info-row"]}>
                                    <MapPin width={16} height={16} />
                                    <span>{group.court_name}</span>
                                </div>
                            )}
                        </div>

                        <div className={styles["price-row"]}>
                            <span>Valor por jogador</span>
                            <strong>{formatPriceCents(group.spot_price)}</strong>
                        </div>

                        <div className={styles["group-card"]}>
                            <div className={styles["group-head"]}>
                                <h3><Users width={14} height={14} /> Jogadores confirmados</h3>
                                <span className={styles["group-count"]}>
                                    {group.filled_spots}<small>/{group.total_spots}</small>
                                </span>
                            </div>

                            <div className={styles["progress"]}>
                                <div className={styles["bar"]}>
                                    <div
                                        className={styles["fill"]}
                                        style={{ width: `${Math.min(100, Math.round((group.filled_spots / group.total_spots) * 100))}%` }}
                                    />
                                </div>
                                <span className={styles["left"]}>{spotsLeft} vagas</span>
                            </div>

                            {group.members.length > 0 ? (
                                <ul className={styles["members"]}>
                                    {group.members.map((m) => (
                                        <li key={m.id} className={styles["member"]}>
                                            <span className={styles["member-avatar"]}>{initials(m.user_name)}</span>
                                            <span className={styles["member-name"]}>{m.user_name ?? `Usuário #${m.user_id}`}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className={styles["members-empty"]}>Nenhum participante confirmado ainda.</p>
                            )}
                        </div>

                        {friendlyError && <p className={styles["error"]}>{friendlyError}</p>}

                        {mode === "manage" ? (
                            <button
                                onClick={() => setConfirmingLeave(true)}
                                disabled={leave.isPending}
                                className={styles["leave-btn"]}
                            >
                                {leave.isPending ? "Saindo..." : "Sair do grupo"}
                            </button>
                        ) : (
                            <button
                                onClick={handleJoin}
                                disabled={join.isPending || spotsLeft === 0 || group.status !== "OPEN"}
                                className={styles["join-btn"]}
                            >
                                {join.isPending ? "Entrando..." : spotsLeft === 0 ? "Sem vagas" : "Entrar na Partida"}
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>

        <ConfirmModal
            open={confirmingLeave}
            icon={<Ban width={22} height={22} />}
            title="Sair do grupo?"
            message="Você vai perder sua vaga nessa partida. Se ainda houver reembolso disponível, o valor pago será estornado."
            confirmLabel="Sair do grupo"
            cancelLabel="Voltar"
            danger
            onConfirm={handleLeave}
            onCancel={() => setConfirmingLeave(false)}
        />
        </>
    );
}

export default JoinGroupModal;
