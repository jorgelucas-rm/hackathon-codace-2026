import { useState } from "react";
import {
    MapPin, Search, SlidersHorizontal, Calendar, Clock, Users, ArrowRight,
    ChevronRight, Star, Moon, Sun, User, Trophy, Activity,
} from "lucide-react";
import { Screen } from "../../types";
import { formatPriceCents } from "../../services/companies.service";
import { formatHHMM, formatPriceCents as formatCents } from "../../services/booking.service";
import { useMe } from "../../hooks/useMe";
import { useCompanySearch, useSports } from "../../hooks/useCompanies";
import { useMyGroups, useOpenGroups } from "../../hooks/useGroups";
import { useMyBookings } from "../Match/hooks/useBookings";
import { getSportIcon } from "../../components/icons/SportIcons";
import { JoinGroupModal } from "../../components/JoinGroupModal/JoinGroupModal";
import { AnimatedSearchInput } from "../../components/AnimatedSearchInput/AnimatedSearchInput";
import styles from "./Home.module.scss";

function formatMatchDate(date: string): string {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

function formatNextMatchDate(date: string): string {
    const [y, m, d] = date.split("-").map(Number);
    const target = new Date(y, m - 1, d);
    const today = new Date();
    return target.toDateString() === today.toDateString()
        ? "Hoje"
        : target.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

interface HomeProps {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
    onSelectSport: (sportId: number) => void;
    onSearch: (term: string) => void;
    onGroupJoined: (paymentId: number) => void;
    onOpenAppointment: (kind: "booking" | "group", id: number) => void;
    dark: boolean;
    toggleDark: () => void;
}

const ACTIVE_GROUP_STATUSES = new Set(["OPEN", "FULL", "CONFIRMED"]);

function dateTimeKey(date: string, time: string): string {
    return `${date}T${time}`;
}

export function Home({ onNavigate, onSelectCourt, onSelectSport, onSearch, onGroupJoined, onOpenAppointment, dark, toggleDark }: HomeProps) {
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
    const { data: sports } = useSports();
    const { data: companiesPage } = useCompanySearch({ size: 6 });
    const recommended = companiesPage?.items ?? [];
    const { data: openGroups } = useOpenGroups();
    const matches = (openGroups ?? []).slice(0, 4);
    const { data: me } = useMe();
    const firstName = me?.entity?.name?.split(" ")[0] ?? "";
    const { data: upcomingBookings } = useMyBookings("upcoming");
    const { data: myGroups } = useMyGroups();

    // "Próxima partida" cobre tanto reservas próprias quanto grupos em que o
    // usuário só entrou como membro (não aparecem em `useMyBookings` — a API
    // de reservas só lista quem criou a reserva) — pega a mais próxima dos dois.
    const nextBooking = upcomingBookings?.[0] ?? null;
    const nextGroup = (myGroups ?? [])
        .filter((g) => ACTIVE_GROUP_STATUSES.has(g.status))
        .sort((a, b) => dateTimeKey(a.date, a.start_time).localeCompare(dateTimeKey(b.date, b.start_time)))[0] ?? null;

    const nextAppointment = !nextBooking ? (nextGroup && { kind: "group" as const, data: nextGroup })
        : !nextGroup ? { kind: "booking" as const, data: nextBooking }
        : dateTimeKey(nextBooking.date, nextBooking.start_time) <= dateTimeKey(nextGroup.date, nextGroup.start_time)
            ? { kind: "booking" as const, data: nextBooking }
            : { kind: "group" as const, data: nextGroup };
    const avatarUrl = me?.entity?.avatar;

    return (
        <div className={styles["container"]}>
            {/* ---------- Header compacto + busca (elemento principal) ---------- */}
            <header className={styles["header"]}>
                <div className={styles["header-glow"]} />
                <div className={styles["inner"]}>
                    <div className={styles["header-top"]}>
                        <div>
                            <p className={styles["location"]}><MapPin width={13} height={13} /> Fortaleza, CE</p>
                            <h1 className={styles["greeting"]}>Olá{firstName ? `, ${firstName}` : ""} <span>👋</span></h1>
                        </div>
                        <div className={styles["actions"]}>
                            <button onClick={toggleDark} className={styles["icon-btn"]} aria-label="Alternar tema">
                                {dark ? <Sun width={18} height={18} /> : <Moon width={18} height={18} />}
                            </button>
                            <button onClick={() => onNavigate("profile")} className={styles["avatar"]} aria-label="Perfil">
                                {avatarUrl ? <img src={avatarUrl} alt="Perfil" /> : <User width={20} height={20} />}
                            </button>
                        </div>
                    </div>

                    <form
                        className={styles["search"]}
                        onSubmit={(e) => { e.preventDefault(); onSearch(searchTerm); }}
                    >
                        <Search width={20} height={20} />
                        <AnimatedSearchInput
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        <button type="submit" className={styles["search-btn"]} aria-label="Filtrar">
                            <SlidersHorizontal width={18} height={18} />
                        </button>
                    </form>
                </div>
            </header>

            <main className={styles["inner"]}>
                {/* ---------- Próxima partida (ação prioritária) ---------- */}
                {nextAppointment && (
                    <section className={styles["next-wrap"]}>
                        <div
                            className={styles["next-card"]}
                            onClick={() => onOpenAppointment(nextAppointment.kind, nextAppointment.data.id)}
                        >
                            <div className={styles["next-icon"]}><Calendar width={22} height={22} /></div>
                            <div className={styles["next-info"]}>
                                <span className={styles["eyebrow"]}>Sua próxima partida</span>
                                <p className={styles["next-title"]}>
                                    {formatNextMatchDate(nextAppointment.data.date)}, {formatHHMM(nextAppointment.data.start_time)}
                                    {" · "}
                                    {nextAppointment.kind === "booking"
                                        ? nextAppointment.data.sport_names[0] ?? nextAppointment.data.court_name ?? "Partida"
                                        : nextAppointment.data.court_name ?? "Partida"}
                                </p>
                                <p className={styles["next-sub"]}>
                                    <MapPin width={13} height={13} /> {[nextAppointment.data.court_name, nextAppointment.data.company_name].filter(Boolean).join(" · ")}
                                </p>
                            </div>
                            <button className={styles["next-cta"]}>Ver <ArrowRight width={16} height={16} /></button>
                        </div>
                    </section>
                )}

                {/* ---------- Esportes ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["row-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Modalidades</span>
                            <h2 className={styles["section-title"]}>Qual esporte hoje?</h2>
                        </div>
                    </div>
                    <div className={styles["sports-grid"]}>
                        {(sports ?? []).map((sport) => (
                            <button key={sport.id} onClick={() => onSelectSport(sport.id)} className={styles["sport-tile"]}>
                                <span className={styles["sport-icon"]}>{getSportIcon(sport.name, { width: 20, height: 20 }) ?? <Trophy width={20} height={20} />}</span>
                                <span className={styles["sport-name"]}>{sport.name}</span>
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
                        <button onClick={() => onNavigate("openMatches")} className={styles["see-all"]}>
                            Ver todas <ChevronRight width={15} height={15} />
                        </button>
                    </div>
                    <div className={styles["matches-grid"]}>
                        {matches.map((match) => {
                            const pct = Math.round((match.filled_spots / match.total_spots) * 100);
                            const spotsLeft = Math.max(0, match.total_spots - match.filled_spots);
                            return (
                                <article key={match.id} onClick={() => setSelectedGroupId(match.id)} className={styles["match-card"]}>
                                    <div className={styles["match-top"]}>
                                        <span className={styles["match-sport"]}><Activity width={18} height={18} /></span>
                                        <span className={styles["level-chip"]}>{formatMatchDate(match.date)}</span>
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
                                        <span className={styles["price"]}>{formatCents(match.spot_price)}</span>
                                        <span className={styles["spots"]}>{spotsLeft} vagas</span>
                                    </div>
                                </article>
                            );
                        })}

                        {matches.length === 0 && <p>Nenhuma partida aberta no momento.</p>}
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
                        {recommended.map((company) => (
                            <article
                                key={company.id}
                                onClick={() => { onSelectCourt(company.id); onNavigate("courtDetail"); }}
                                className={styles["court-card"]}
                            >
                                <div
                                    className={styles["court-img"]}
                                    style={company.cover_photo
                                        ? { backgroundImage: `url(${company.cover_photo})`, backgroundSize: "cover", backgroundPosition: "center" }
                                        : { background: "linear-gradient(135deg, rgba(173,153,0,0.15), #E8D7BD)" }}
                                >
                                    {!company.cover_photo && <Trophy width={46} height={46} />}
                                    {company.distance_km !== null && (
                                        <span className={styles["court-distance"]}><MapPin width={12} height={12} /> {company.distance_km.toFixed(1)} km</span>
                                    )}
                                </div>
                                <div className={styles["court-body"]}>
                                    <div className={styles["court-head"]}>
                                        <p className={styles["court-name"]}>{company.name}</p>
                                        <span className={styles["rating-badge"]}>
                                            <Star width={14} height={14} />
                                            {company.nota_media !== null ? company.nota_media.toFixed(1) : "novo"}
                                        </span>
                                    </div>
                                    <p className={styles["court-place"]}>
                                        <MapPin width={12} height={12} /> {[company.neighborhood, company.city].filter(Boolean).join(", ")}
                                    </p>
                                    {company.sports.length > 0 && (
                                        <div className={styles["court-tags"]}>
                                            {company.sports.map((sport) => (
                                                <span key={sport.id} className={styles["tag"]}>
                                                    {getSportIcon(sport.name, { width: 12, height: 12 })}
                                                    {sport.name}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                    <div className={styles["court-foot"]}>
                                        <div className={styles["price-block"]}>
                                            <span className={styles["price-eyebrow"]}>A partir de</span>
                                            <span className={styles["price"]}>{formatPriceCents(company.min_price_hour)}{company.min_price_hour !== null ? "/h" : ""}</span>
                                        </div>
                                    </div>
                                </div>
                            </article>
                        ))}

                        {recommended.length === 0 && <p>Nenhuma arena cadastrada ainda.</p>}
                    </div>
                </section>
            </main>

            <footer className={styles["footer"]}>
                <p>© 2026 Reservaê · Fortaleza, CE</p>
            </footer>

            <JoinGroupModal
                groupId={selectedGroupId}
                onClose={() => setSelectedGroupId(null)}
                onJoined={(paymentId) => { setSelectedGroupId(null); onGroupJoined(paymentId); }}
            />
        </div>
    );
}

export default Home;
