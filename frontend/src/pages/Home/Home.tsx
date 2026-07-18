import { useState } from "react";
import {
    MapPin, Search, SlidersHorizontal, Calendar, Clock, Users, ArrowRight,
    ChevronRight, Star, Moon, Sun, User, Plus,
    CircleDot, Activity, Dumbbell, Zap, Volleyball, Waves, Trophy,
} from "lucide-react";
import { Screen } from "../../types";
import { getCourtsSync } from "../../services/courts.service";
import { getOpenMatchesSync } from "../../services/matches.service";
import styles from "./Home.module.scss";

interface HomeProps {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
    onSearch: (term: string) => void;
    dark: boolean;
    toggleDark: () => void;
}

const SPORTS = [
    { Icon: CircleDot, name: "Futebol", courts: 24 },
    { Icon: Activity, name: "Futsal", courts: 18 },
    { Icon: Dumbbell, name: "Basquete", courts: 9 },
    { Icon: Zap, name: "Vôlei", courts: 11 },
    { Icon: Volleyball, name: "Tênis", courts: 16 },
    { Icon: Waves, name: "Beach Tennis", courts: 14 },
    { Icon: Trophy, name: "Padel", courts: 7 },
    { Icon: Plus, name: "Outros", courts: 15 },
];

export function Home({ onNavigate, onSelectCourt, onSearch, dark, toggleDark }: HomeProps) {
    const [searchTerm, setSearchTerm] = useState("");
    const courts = getCourtsSync();
    const matches = getOpenMatchesSync();
    const recommended = courts.slice(0, 6);

    return (
        <div className={styles["container"]}>
            {/* ---------- Header compacto + busca (elemento principal) ---------- */}
            <header className={styles["header"]}>
                <div className={styles["header-glow"]} />
                <div className={styles["inner"]}>
                    <div className={styles["header-top"]}>
                        <div>
                            <p className={styles["location"]}><MapPin width={13} height={13} /> Fortaleza, CE</p>
                            <h1 className={styles["greeting"]}>Olá, João <span>👋</span></h1>
                        </div>
                        <div className={styles["actions"]}>
                            <button onClick={toggleDark} className={styles["icon-btn"]} aria-label="Alternar tema">
                                {dark ? <Sun width={18} height={18} /> : <Moon width={18} height={18} />}
                            </button>
                            <button onClick={() => onNavigate("profile")} className={styles["avatar"]} aria-label="Perfil">
                                <User width={20} height={20} />
                            </button>
                        </div>
                    </div>

                    <form
                        className={styles["search"]}
                        onSubmit={(e) => { e.preventDefault(); onSearch(searchTerm); }}
                    >
                        <Search width={20} height={20} />
                        <input
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Buscar quadras, esportes ou locais..."
                        />
                        <button type="submit" className={styles["search-btn"]} aria-label="Filtrar">
                            <SlidersHorizontal width={18} height={18} />
                        </button>
                    </form>
                </div>
            </header>

            <main className={styles["inner"]}>
                {/* ---------- Próxima partida (ação prioritária) ---------- */}
                <section className={styles["next-wrap"]}>
                    <div className={styles["next-card"]} onClick={() => onNavigate("schedule")}>
                        <div className={styles["next-icon"]}><Calendar width={22} height={22} /></div>
                        <div className={styles["next-info"]}>
                            <span className={styles["eyebrow"]}>Sua próxima partida</span>
                            <p className={styles["next-title"]}>Hoje, 20:00 · Futebol Society</p>
                            <p className={styles["next-sub"]}><MapPin width={13} height={13} /> Arena Prime Futebol · Aldeota</p>
                        </div>
                        <button className={styles["next-cta"]}>Ver <ArrowRight width={16} height={16} /></button>
                    </div>
                </section>

                {/* ---------- Esportes ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["row-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Modalidades</span>
                            <h2 className={styles["section-title"]}>Qual esporte hoje?</h2>
                        </div>
                    </div>
                    <div className={styles["sports-grid"]}>
                        {SPORTS.map((sport) => (
                            <button key={sport.name} onClick={() => onNavigate("courts")} className={styles["sport-tile"]}>
                                <span className={styles["sport-icon"]}><sport.Icon width={20} height={20} /></span>
                                <span className={styles["sport-name"]}>{sport.name}</span>
                                <span className={styles["sport-count"]}>{sport.courts} quadras</span>
                            </button>
                        ))}
                    </div>
                </section>

                {/* ---------- Partidas abertas próximas ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["row-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Bora jogar</span>
                            <h2 className={styles["section-title"]}>Partidas abertas perto</h2>
                        </div>
                        <button onClick={() => onNavigate("match")} className={styles["see-all"]}>
                            Ver todas <ChevronRight width={15} height={15} />
                        </button>
                    </div>
                    <div className={styles["matches-grid"]}>
                        {matches.map((match, i) => {
                            const pct = Math.round((match.players / match.maxPlayers) * 100);
                            return (
                                <article key={i} onClick={() => onNavigate("match")} className={styles["match-card"]}>
                                    <div className={styles["match-top"]}>
                                        <span className={styles["match-sport"]}><Activity width={18} height={18} /></span>
                                        <span className={styles["level-chip"]}>{match.level}</span>
                                    </div>
                                    <p className={styles["match-name"]}>{match.name}</p>
                                    <p className={styles["match-place"]}><MapPin width={12} height={12} /> {match.location}</p>
                                    <p className={styles["match-time"]}><Clock width={12} height={12} /> {match.time}</p>
                                    <div className={styles["progress-wrap"]}>
                                        <div className={styles["progress-bar"]}>
                                            <div style={{ width: `${pct}%` }} />
                                        </div>
                                        <span className={styles["progress-text"]}><Users width={12} height={12} /> {match.players}/{match.maxPlayers}</span>
                                    </div>
                                    <div className={styles["match-foot"]}>
                                        <span className={styles["price"]}>{match.price}</span>
                                        <span className={styles["spots"]}>{match.spots} vagas</span>
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                </section>

                {/* ---------- Quadras recomendadas ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["row-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Selecionadas para você</span>
                            <h2 className={styles["section-title"]}>Quadras recomendadas</h2>
                        </div>
                        <button onClick={() => onNavigate("courts")} className={styles["see-all"]}>
                            Ver todas <ChevronRight width={15} height={15} />
                        </button>
                    </div>
                    <div className={styles["courts-grid"]}>
                        {recommended.map((court) => (
                            <article
                                key={court.id}
                                onClick={() => { onSelectCourt(court.id); onNavigate("courtDetail"); }}
                                className={styles["court-card"]}
                            >
                                <div className={styles["court-img"]} style={{ background: court.gradient }}>
                                    <Trophy width={46} height={46} />
                                    {court.premium && <span className={styles["premium-tag"]}>PREMIUM</span>}
                                    <span className={styles["court-distance"]}><MapPin width={12} height={12} /> {court.distance}</span>
                                </div>
                                <div className={styles["court-body"]}>
                                    <div className={styles["court-head"]}>
                                        <p className={styles["court-name"]}>{court.name}</p>
                                        <span className={styles["rating-badge"]}><Star width={14} height={14} /> {court.rating}</span>
                                    </div>
                                    <p className={styles["court-place"]}>{court.neighborhood}</p>
                                    <div className={styles["court-tags"]}>
                                        {court.sportTags.map((t) => <span key={t} className={styles["tag"]}>{t}</span>)}
                                    </div>
                                    <div className={styles["court-foot"]}>
                                        <span className={styles["price"]}>{court.price}</span>
                                        <span className={styles["review-count"]}>{court.reviewCount} avaliações</span>
                                    </div>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            </main>

            <footer className={styles["footer"]}>
                <p>© 2026 Reservaê · Fortaleza, CE</p>
            </footer>
        </div>
    );
}

export default Home;
