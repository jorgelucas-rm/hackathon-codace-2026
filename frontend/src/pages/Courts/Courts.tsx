import { useState } from "react";
import { MapPin, Search, SlidersHorizontal, X, Heart, Navigation, Trophy, Star, ArrowUpDown, ArrowRight } from "lucide-react";
import { Screen } from "../../types";
import { getCourtsSync } from "../../services/courts.service";
import styles from "./Courts.module.scss";

interface CourtsProps {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
    initialSearch?: string;
}

const SPORT_FILTERS = ["Todos", "Beach Tennis", "Futebol", "Futsal", "Basquete", "Tênis", "Padel"];

export function Courts({ onNavigate, onSelectCourt, initialSearch = "" }: CourtsProps) {
    const [search, setSearch] = useState(initialSearch);
    const [activeFilter, setActiveFilter] = useState("Todos");
    const [favs, setFavs] = useState<number[]>([]);
    const courts = getCourtsSync();

    const filtered = courts.filter((c) => {
        const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.neighborhood.toLowerCase().includes(search.toLowerCase());
        const matchFilter = activeFilter === "Todos" || c.sports.some((s) => s.toLowerCase().includes(activeFilter.toLowerCase()));
        return matchSearch && matchFilter;
    });

    const toggleFav = (id: number) => {
        setFavs((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
    };

    const slotClass = (status: string) => {
        if (status === "reservado" || status === "privada" || status === "indisponivel") return styles["slot-busy"];
        if (status === "ultimas") return styles["slot-last"];
        return styles["slot-free"];
    };

    return (
        <div className={styles["container"]}>
            {/* ---------- Topo: título + busca principal + filtros ---------- */}
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <div className={styles["header-top"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Descobrir</span>
                            <h1 className={styles["title"]}>Quadras em Fortaleza</h1>
                        </div>
                        <p className={styles["location"]}><MapPin width={13} height={13} /> Fortaleza, CE</p>
                    </div>

                    <div className={styles["search"]}>
                        <Search width={20} height={20} />
                        <input
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Buscar por nome, bairro ou local..."
                        />
                        {search
                            ? <button onClick={() => setSearch("")} className={styles["clear"]} aria-label="Limpar"><X width={16} height={16} /></button>
                            : null}
                        <button className={styles["search-btn"]} aria-label="Filtros"><SlidersHorizontal width={18} height={18} /></button>
                    </div>

                    <div className={`scrollbar-none ${styles["filters-row"]}`}>
                        {SPORT_FILTERS.map((f) => (
                            <button
                                key={f}
                                onClick={() => setActiveFilter(f)}
                                className={`${styles["filter"]} ${activeFilter === f ? styles["filter-active"] : ""}`}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            <main className={styles["inner"]}>
                <div className={styles["results-head"]}>
                    <p className={styles["results-count"]}><strong>{filtered.length}</strong> quadras encontradas</p>
                    <button className={styles["sort-btn"]}><ArrowUpDown width={14} height={14} /> Ordenar</button>
                </div>

                <div className={styles["grid"]}>
                    {filtered.map((court) => (
                        <article
                            key={court.id}
                            onClick={() => { onSelectCourt(court.id); onNavigate("courtDetail"); }}
                            className={styles["court-card"]}
                        >
                            <div className={styles["court-img"]} style={{ background: court.gradient }}>
                                <Trophy width={52} height={52} />
                                <div className={styles["img-fade"]} />
                                {court.premium && <span className={styles["premium-tag"]}>PREMIUM</span>}
                                <button
                                    onClick={(e) => { e.stopPropagation(); toggleFav(court.id); }}
                                    className={`${styles["fav"]} ${favs.includes(court.id) ? styles["fav-active"] : ""}`}
                                    aria-label="Favoritar"
                                >
                                    <Heart width={16} height={16} />
                                </button>
                                <div className={styles["tags"]}>
                                    {court.sportTags.map((tag) => <span key={tag}>{tag}</span>)}
                                </div>
                            </div>

                            <div className={styles["court-body"]}>
                                <div className={styles["court-head"]}>
                                    <div className={styles["court-id"]}>
                                        <h3 className={styles["court-name"]}>{court.name}</h3>
                                        <p className={styles["court-place"]}><MapPin width={12} height={12} /> {court.neighborhood.split(",")[0]}</p>
                                    </div>
                                    <span className={styles["rating-badge"]}><Star width={13} height={13} /> {court.rating}</span>
                                </div>

                                <div className={styles["meta-row"]}>
                                    <span className={styles["reviews"]}>{court.reviewCount} avaliações</span>
                                    <span className={styles["distance"]}><Navigation width={12} height={12} /> {court.distance}</span>
                                </div>

                                <div className={styles["slots-row"]}>
                                    <span className={styles["slot-label"]}>Hoje</span>
                                    {court.todaySlots.slice(0, 3).map((slot) => (
                                        <span key={slot.time} className={`${styles["slot"]} ${slotClass(slot.status)}`}>
                                            {slot.time}
                                        </span>
                                    ))}
                                </div>

                                <div className={styles["court-foot"]}>
                                    <div className={styles["price-block"]}>
                                        <span className={styles["eyebrow"]}>A partir de</span>
                                        <strong className={styles["price"]}>{court.price}</strong>
                                    </div>
                                    <span className={styles["go-btn"]}><ArrowRight width={16} height={16} /></span>
                                </div>
                            </div>
                        </article>
                    ))}

                    {filtered.length === 0 && (
                        <div className={styles["empty"]}>
                            <Search width={44} height={44} className={styles["empty-icon"]} />
                            <p>Nenhuma quadra encontrada</p>
                            <button onClick={() => { setSearch(""); setActiveFilter("Todos"); }}>Limpar filtros</button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default Courts;
