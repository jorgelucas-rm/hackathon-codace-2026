import { useState } from "react";
import { ChevronLeft, Clock, Calendar, MapPin, Users, ArrowRight, ChevronRight, Award, Timer, LayoutGrid, CircleDot, Activity, Volleyball, Waves, Dumbbell } from "lucide-react";
import { Screen } from "../../types";
import { getOpenMatchesSync } from "../../services/matches.service";
import styles from "./Match.module.scss";

interface MatchProps {
    onNavigate: (screen: Screen) => void;
}

const PLAYERS = ["LC", "MF", "AF", "VI", "CA", "AP", "JO"];

type ApptTab = "proximos" | "concluidos" | "cancelados";

const APPT_TABS: { key: ApptTab; label: string }[] = [
    { key: "proximos", label: "Próximos" },
    { key: "concluidos", label: "Concluídos" },
    { key: "cancelados", label: "Cancelados" },
];

const APPOINTMENTS: Record<ApptTab, { Icon: typeof CircleDot; name: string; date: string; time: string; price: string; status: string; kind: "upcoming" | "done" | "cancel" }[]> = {
    proximos: [
        { Icon: CircleDot, name: "Futebol Society — Quinta", date: "12 jul", time: "20:00", price: "R$25", status: "Confirmado", kind: "upcoming" },
        { Icon: Waves, name: "Beach Tennis Duplas", date: "15 jul", time: "18:00", price: "R$35", status: "Confirmado", kind: "upcoming" },
    ],
    concluidos: [
        { Icon: Volleyball, name: "Vôlei Praia", date: "10 jul", time: "17:00", price: "R$70", status: "Concluído", kind: "done" },
        { Icon: Activity, name: "Futsal — Quarta", date: "05 jul", time: "19:00", price: "R$20", status: "Concluído", kind: "done" },
    ],
    cancelados: [
        { Icon: Dumbbell, name: "Basquete 3x3", date: "02 jul", time: "09:00", price: "R$20", status: "Cancelado", kind: "cancel" },
    ],
};

export function Match({ onNavigate }: MatchProps) {
    const match = getOpenMatchesSync()[0];
    const pct = Math.round((PLAYERS.length / match.maxPlayers) * 100);
    const [apptTab, setApptTab] = useState<ApptTab>("proximos");
    const appointments = APPOINTMENTS[apptTab];
    const badgeClass = { upcoming: "badge-upcoming", done: "badge-done", cancel: "badge-cancel" };

    return (
        <div className={styles["container"]}>
            {/* ---------- Top bar compacto (bege, integrado) ---------- */}
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <button onClick={() => onNavigate("home")} className={styles["back"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <span className={styles["header-label"]}>Detalhes da partida</span>
                </div>
            </header>

            <main className={styles["inner"]}>
                {/* ---------- Card principal: tudo pra decidir ---------- */}
                <section className={styles["hero-card"]}>
                    <div className={styles["badges"]}>
                        <span className={styles["open-badge"]}><i className={styles["dot"]} /> Grupo Aberto</span>
                        <span className={styles["level-chip"]}>{match.level}</span>
                    </div>

                    <h1 className={styles["title"]}>{match.name}</h1>

                    <div className={styles["meta"]}>
                        <span className={styles["meta-item"]}><Calendar width={16} height={16} /> Hoje</span>
                        <span className={styles["meta-item"]}><Clock width={16} height={16} /> {match.time}</span>
                        <span className={styles["meta-item"]}><MapPin width={16} height={16} /> {match.location} · Aldeota</span>
                    </div>

                    <div className={styles["price-row"]}>
                        <div className={styles["price-block"]}>
                            <span className={styles["eyebrow"]}>Valor por jogador</span>
                            <strong className={styles["price"]}>{match.price.replace("/jogador", "")}</strong>
                        </div>
                        <span className={styles["status-pill"]}><i className={styles["dot-ok"]} /> {match.spots} vagas restantes</span>
                    </div>
                </section>

                {/* ---------- Jogadores confirmados (compacto) ---------- */}
                <section className={styles["players-card"]}>
                    <div className={styles["players-head"]}>
                        <h3>Jogadores confirmados</h3>
                        <span className={styles["count"]}>{PLAYERS.length}<small>/{match.maxPlayers}</small></span>
                    </div>

                    <div className={styles["avatars-row"]}>
                        {PLAYERS.map((p) => (
                            <span key={p} className={styles["avatar-p"]}>{p}</span>
                        ))}
                        <span className={styles["slot-more"]}>+{match.spots}</span>
                    </div>

                    <div className={styles["progress"]}>
                        <div className={styles["bar"]}><div className={styles["fill"]} style={{ width: `${pct}%` }} /></div>
                        <span className={styles["left"]}>{match.spots} vagas</span>
                    </div>
                </section>

                {/* ---------- CTA principal ---------- */}
                <button onClick={() => onNavigate("checkout")} className={styles["join"]}>
                    Entrar na Partida <ArrowRight width={18} height={18} />
                </button>

                {/* ---------- Sobre a partida (destaque) ---------- */}
                <section className={styles["about-card"]}>
                    <span className={styles["eyebrow"]}>Sobre</span>
                    <h3 className={styles["about-title"]}>Sobre a partida</h3>
                    <p className={styles["about-text"]}>
                        Jogo semanal na Arena Prime Futebol. Nível intermediário, aberto a todos.
                        Chegue 15 minutos antes para aquecer. Colete e bola por conta da casa.
                    </p>
                    <div className={styles["facts"]}>
                        <div className={styles["fact"]}>
                            <Award width={16} height={16} />
                            <span className={styles["fact-label"]}>Nível</span>
                            <strong>{match.level}</strong>
                        </div>
                        <div className={styles["fact"]}>
                            <Timer width={16} height={16} />
                            <span className={styles["fact-label"]}>Duração</span>
                            <strong>1h30</strong>
                        </div>
                        <div className={styles["fact"]}>
                            <LayoutGrid width={16} height={16} />
                            <span className={styles["fact-label"]}>Formato</span>
                            <strong>Society 7</strong>
                        </div>
                    </div>
                </section>

                {/* ---------- Localização (leve e compacta) ---------- */}
                <section className={styles["loc-card"]}>
                    <span className={styles["loc-icon"]}><MapPin width={18} height={18} /></span>
                    <div className={styles["loc-text"]}>
                        <p>{match.location}</p>
                        <span>Av. Santos Dumont, 5532 · Aldeota, Fortaleza — CE</span>
                    </div>
                    <ChevronRight width={18} height={18} className={styles["loc-chevron"]} />
                </section>

                {/* ---------- Meus agendamentos ---------- */}
                <section className={styles["appointments"]}>
                    <div className={styles["appt-head"]}>
                        <span className={styles["eyebrow"]}>Suas partidas</span>
                        <h2 className={styles["appt-title"]}>Meus agendamentos</h2>
                    </div>

                    <div className={`scrollbar-none ${styles["tabs"]}`}>
                        {APPT_TABS.map((t) => (
                            <button
                                key={t.key}
                                onClick={() => setApptTab(t.key)}
                                className={`${styles["tab"]} ${apptTab === t.key ? styles["tab-active"] : ""}`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>

                    <div className={styles["appt-list"]}>
                        {appointments.length > 0 ? appointments.map((a, i) => (
                            <div key={i} className={styles["appt-card"]}>
                                <span className={styles["appt-icon"]}><a.Icon width={20} height={20} /></span>
                                <div className={styles["appt-info"]}>
                                    <p className={styles["appt-name"]}>{a.name}</p>
                                    <p className={styles["appt-sub"]}>{a.date} · {a.time} · {a.price}</p>
                                </div>
                                <span className={`${styles["badge"]} ${styles[badgeClass[a.kind]]}`}>{a.status}</span>
                            </div>
                        )) : (
                            <p className={styles["appt-empty"]}>Nenhuma partida nesta categoria.</p>
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
}

export default Match;
