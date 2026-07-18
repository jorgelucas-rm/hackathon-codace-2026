import { useState } from "react";
import { ChevronLeft, Loader2, MapPin, Clock, Users, Activity } from "lucide-react";
import { Screen } from "../../types";
import { formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useOpenGroups } from "../../hooks/useGroups";
import { JoinGroupModal } from "../../components/JoinGroupModal/JoinGroupModal";
import styles from "./OpenMatches.module.scss";

interface OpenMatchesProps {
    onNavigate: (screen: Screen) => void;
    onGroupJoined: (paymentId: number) => void;
}

function formatShortDate(date: string): string {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

export function OpenMatches({ onNavigate, onGroupJoined }: OpenMatchesProps) {
    const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
    const { data: groups, isLoading, isError } = useOpenGroups();

    return (
        <div className={styles["container"]}>
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <button onClick={() => onNavigate("home")} className={styles["back"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <span className={styles["header-label"]}>Partidas abertas</span>
                </div>
            </header>

            <main className={styles["inner"]}>
                <section className={styles["section"]}>
                    <div className={styles["section-head"]}>
                        <span className={styles["eyebrow"]}>Bora jogar</span>
                        <h2 className={styles["section-title"]}>Partidas abertas perto de você</h2>
                    </div>

                    {isLoading && (
                        <div className={styles["state"]}>
                            <Loader2 width={20} height={20} className={styles["spin"]} />
                            <span>Carregando partidas...</span>
                        </div>
                    )}

                    {isError && !isLoading && (
                        <p className={styles["empty"]}>Não foi possível carregar as partidas abertas agora.</p>
                    )}

                    {!isLoading && !isError && (
                        <div className={styles["matches-grid"]}>
                            {(groups ?? []).map((match) => {
                                const pct = Math.round((match.filled_spots / match.total_spots) * 100);
                                const spotsLeft = Math.max(0, match.total_spots - match.filled_spots);
                                return (
                                    <article
                                        key={match.id}
                                        onClick={() => setSelectedGroupId(match.id)}
                                        className={styles["match-card"]}
                                    >
                                        <div className={styles["match-top"]}>
                                            <span className={styles["match-sport"]}><Activity width={18} height={18} /></span>
                                            <span className={styles["level-chip"]}>{formatShortDate(match.date)}</span>
                                        </div>
                                        <p className={styles["match-name"]}>{match.court_name ?? "Partida aberta"}</p>
                                        {match.company_name && (
                                            <p className={styles["match-place"]}><MapPin width={12} height={12} /> {match.company_name}</p>
                                        )}
                                        <p className={styles["match-time"]}><Clock width={12} height={12} /> {formatHHMM(match.start_time)} – {formatHHMM(match.end_time)}</p>
                                        <div className={styles["progress-wrap"]}>
                                            <div className={styles["progress-bar"]}>
                                                <div style={{ width: `${pct}%` }} />
                                            </div>
                                            <span className={styles["progress-text"]}><Users width={12} height={12} /> {match.filled_spots}/{match.total_spots}</span>
                                        </div>
                                        <div className={styles["match-foot"]}>
                                            <span className={styles["price"]}>{formatPriceCents(match.spot_price)}</span>
                                            <span className={styles["spots"]}>{spotsLeft} vagas</span>
                                        </div>
                                    </article>
                                );
                            })}

                            {(groups ?? []).length === 0 && <p className={styles["empty"]}>Nenhuma partida aberta no momento.</p>}
                        </div>
                    )}
                </section>
            </main>

            <JoinGroupModal
                groupId={selectedGroupId}
                onClose={() => setSelectedGroupId(null)}
                onJoined={(paymentId) => { setSelectedGroupId(null); onGroupJoined(paymentId); }}
            />
        </div>
    );
}

export default OpenMatches;
