import { useEffect, useState } from "react";
import { MapPin, Search, SlidersHorizontal, X, Heart, Navigation, Trophy, Star, ArrowRight, Loader2 } from "lucide-react";
import { Screen } from "../../types";
import { formatPriceCents } from "../../services/companies.service";
import { useCompanySearch, useSports } from "../../hooks/useCompanies";
import { getSportIcon } from "../../components/icons/SportIcons";
import styles from "./Courts.module.scss";

interface CourtsProps {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
    initialSearch?: string;
    initialSportId?: number | null;
}

export function Courts({ onNavigate, onSelectCourt, initialSearch = "", initialSportId = null }: CourtsProps) {
    const [search, setSearch] = useState(initialSearch);
    const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
    const [activeSportId, setActiveSportId] = useState<number | null>(initialSportId);
    const [favs, setFavs] = useState<number[]>([]);

    // Debounce da busca por texto — evita 1 request por tecla digitada.
    useEffect(() => {
        const timeout = setTimeout(() => setDebouncedSearch(search), 400);
        return () => clearTimeout(timeout);
    }, [search]);

    const { data: sports } = useSports();
    const {
        data: page,
        isLoading,
        isError,
    } = useCompanySearch({ q: debouncedSearch || undefined, sportId: activeSportId, size: 20 });

    const companies = page?.items ?? [];

    const toggleFav = (id: number) => {
        setFavs((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
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
                        <button
                            onClick={() => setActiveSportId(null)}
                            className={`${styles["filter"]} ${activeSportId === null ? styles["filter-active"] : ""}`}
                        >
                            Todos
                        </button>
                        {(sports ?? []).map((sport) => (
                            <button
                                key={sport.id}
                                onClick={() => setActiveSportId(sport.id)}
                                className={`${styles["filter"]} ${activeSportId === sport.id ? styles["filter-active"] : ""}`}
                            >
                                {getSportIcon(sport.name, { width: 15, height: 15 })}{sport.name}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            <main className={styles["inner"]}>
                <div className={styles["results-head"]}>
                    <p className={styles["results-count"]}><strong>{page?.total_filtered ?? 0}</strong> arenas encontradas</p>
                </div>

                <div className={styles["grid"]}>
                    {companies.map((company) => (
                        <article
                            key={company.id}
                            onClick={() => { onSelectCourt(company.id); onNavigate("courtDetail"); }}
                            className={styles["court-card"]}
                        >
                            <div
                                className={styles["court-img"]}
                                style={company.cover_photo
                                    ? { backgroundImage: `url(${company.cover_photo})`, backgroundSize: "cover", backgroundPosition: "center" }
                                    : { background: "linear-gradient(135deg, rgba(173,153,0,0.2), #E8D7BD)" }}
                            >
                                {!company.cover_photo && <Trophy width={52} height={52} />}
                                <div className={styles["img-fade"]} />
                                <button
                                    onClick={(e) => { e.stopPropagation(); toggleFav(company.id); }}
                                    className={`${styles["fav"]} ${favs.includes(company.id) ? styles["fav-active"] : ""}`}
                                    aria-label="Favoritar"
                                >
                                    <Heart width={16} height={16} />
                                </button>
                            </div>

                            <div className={styles["court-body"]}>
                                <div className={styles["court-head"]}>
                                    <div className={styles["court-id"]}>
                                        <h3 className={styles["court-name"]}>{company.name}</h3>
                                    </div>
                                    <span className={styles["rating-badge"]}>
                                        <Star width={13} height={13} />
                                        {company.nota_media !== null ? company.nota_media.toFixed(1) : "novo"}
                                    </span>
                                </div>

                                <div className={styles["meta-row"]}>
                                    {company.distance_km !== null && (
                                        <span className={styles["distance"]}><Navigation width={12} height={12} /> {company.distance_km.toFixed(1)} km</span>
                                    )}
                                </div>

                                <div className={styles["court-foot"]}>
                                    <div className={styles["price-block"]}>
                                        <span className={styles["eyebrow"]}>A partir de</span>
                                        <strong className={styles["price"]}>{formatPriceCents(company.min_price_hour)}{company.min_price_hour !== null ? "/h" : ""}</strong>
                                    </div>
                                    <span className={styles["go-btn"]}><ArrowRight width={16} height={16} /></span>
                                </div>
                            </div>
                        </article>
                    ))}

                    {isLoading && (
                        <div className={styles["empty"]}>
                            <Loader2 width={36} height={36} className={styles["empty-icon"]} />
                            <p>Buscando arenas...</p>
                        </div>
                    )}

                    {isError && !isLoading && (
                        <div className={styles["empty"]}>
                            <Search width={44} height={44} className={styles["empty-icon"]} />
                            <p>Não foi possível carregar as arenas agora.</p>
                        </div>
                    )}

                    {!isLoading && !isError && companies.length === 0 && (
                        <div className={styles["empty"]}>
                            <Search width={44} height={44} className={styles["empty-icon"]} />
                            <p>Nenhuma arena encontrada</p>
                            <button onClick={() => { setSearch(""); setActiveSportId(null); }}>Limpar filtros</button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default Courts;
