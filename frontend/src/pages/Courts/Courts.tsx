import { useEffect, useState } from "react";
import { MapPin, Search, SlidersHorizontal, X, Heart, Navigation, Trophy, Star, ArrowRight, Loader2 } from "lucide-react";
import { Screen } from "../../types";
import { formatPriceCents } from "../../services/companies.service";
import { useCompanySearch, useSports } from "../../hooks/useCompanies";
import { getSportIcon } from "../../components/icons/SportIcons";
import { AnimatedSearchInput } from "../../components/AnimatedSearchInput/AnimatedSearchInput";
import styles from "./Courts.module.scss";

interface CourtsProps {
    onNavigate: (screen: Screen) => void;
    onSelectCourt: (id: number) => void;
    initialSearch?: string;
    initialSportId?: number | null;
}

type SortOption = "relevancia" | "preco" | "avaliacao";

const PRICE_RANGES: { id: string; label: string; min: number; max: number | null }[] = [
    { id: "ate-50", label: "Até R$ 50/h", min: 0, max: 5000 },
    { id: "50-100", label: "R$ 50 – R$ 100/h", min: 5000, max: 10000 },
    { id: "100-150", label: "R$ 100 – R$ 150/h", min: 10000, max: 15000 },
    { id: "150+", label: "Acima de R$ 150/h", min: 15000, max: null },
];

const AMENITIES_OPTIONS: { id: string; label: string }[] = [
    { id: "estacionamento", label: "Estacionamento" },
    { id: "vestiario", label: "Vestiário" },
    { id: "wifi", label: "Wi-Fi" },
    { id: "lanchonete", label: "Lanchonete" },
    { id: "churrasqueira", label: "Churrasqueira" },
    { id: "loja", label: "Loja" },
];

export function Courts({ onNavigate, onSelectCourt, initialSearch = "", initialSportId = null }: CourtsProps) {
    const [search, setSearch] = useState(initialSearch);
    const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
    const [activeSportId, setActiveSportId] = useState<number | null>(initialSportId);
    const [favs, setFavs] = useState<number[]>([]);

    const [filtersOpen, setFiltersOpen] = useState(false);
    const [sortBy, setSortBy] = useState<SortOption>("relevancia");
    const [city, setCity] = useState<string | null>(null);
    const [priceRangeId, setPriceRangeId] = useState<string | null>(null);
    const [amenities, setAmenities] = useState<string[]>([]);

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
    } = useCompanySearch({ q: debouncedSearch || undefined, sportId: activeSportId, amenities, size: 20 });

    const allCompanies = page?.items ?? [];

    // Cidade e faixa de preço são filtradas no cliente: o endpoint público
    // não tem esses parâmetros (só nome/esporte/comodidades/raio), e a base
    // de demo é pequena o bastante pra isso não pesar.
    const cities = Array.from(new Set(allCompanies.map((c) => c.city).filter(Boolean))).sort();

    const selectedPriceRange = PRICE_RANGES.find((r) => r.id === priceRangeId) ?? null;

    const companies = allCompanies
        .filter((c) => (city ? c.city === city : true))
        .filter((c) => {
            if (!selectedPriceRange || c.min_price_hour === null) return !selectedPriceRange;
            const aboveMin = c.min_price_hour >= selectedPriceRange.min;
            const belowMax = selectedPriceRange.max === null || c.min_price_hour < selectedPriceRange.max;
            return aboveMin && belowMax;
        })
        .sort((a, b) => {
            if (sortBy === "preco") return (a.min_price_hour ?? Infinity) - (b.min_price_hour ?? Infinity);
            if (sortBy === "avaliacao") return (b.nota_media ?? -1) - (a.nota_media ?? -1);
            return 0;
        });

    const activeFilterCount = (city ? 1 : 0) + (priceRangeId ? 1 : 0) + amenities.length + (sortBy !== "relevancia" ? 1 : 0);

    const toggleAmenity = (id: string) => {
        setAmenities((prev) => prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]);
    };

    const clearAllFilters = () => {
        setCity(null);
        setPriceRangeId(null);
        setAmenities([]);
        setSortBy("relevancia");
    };

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
                        <AnimatedSearchInput
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                        {search
                            ? <button onClick={() => setSearch("")} className={styles["clear"]} aria-label="Limpar"><X width={16} height={16} /></button>
                            : null}
                        <button
                            onClick={() => setFiltersOpen((prev) => !prev)}
                            className={`${styles["search-btn"]} ${activeFilterCount > 0 ? styles["search-btn-active"] : ""}`}
                            aria-label="Filtros"
                        >
                            <SlidersHorizontal width={18} height={18} />
                            {activeFilterCount > 0 && <span className={styles["filter-count"]}>{activeFilterCount}</span>}
                        </button>
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

                    {filtersOpen && (
                        <div className={styles["filters-panel"]}>
                            <div className={styles["filter-group"]}>
                                <span className={styles["filter-group-label"]}>Ordenar por</span>
                                <div className={styles["chip-row"]}>
                                    {([
                                        { id: "relevancia", label: "Relevância" },
                                        { id: "preco", label: "Menor preço" },
                                        { id: "avaliacao", label: "Melhor avaliação" },
                                    ] as { id: SortOption; label: string }[]).map((opt) => (
                                        <button
                                            key={opt.id}
                                            onClick={() => setSortBy(opt.id)}
                                            className={`${styles["chip"]} ${sortBy === opt.id ? styles["chip-active"] : ""}`}
                                        >
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {cities.length > 1 && (
                                <div className={styles["filter-group"]}>
                                    <span className={styles["filter-group-label"]}>Cidade</span>
                                    <div className={styles["chip-row"]}>
                                        <button
                                            onClick={() => setCity(null)}
                                            className={`${styles["chip"]} ${city === null ? styles["chip-active"] : ""}`}
                                        >
                                            Todas
                                        </button>
                                        {cities.map((c) => (
                                            <button
                                                key={c}
                                                onClick={() => setCity(c)}
                                                className={`${styles["chip"]} ${city === c ? styles["chip-active"] : ""}`}
                                            >
                                                {c}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className={styles["filter-group"]}>
                                <span className={styles["filter-group-label"]}>Faixa de preço</span>
                                <div className={styles["chip-row"]}>
                                    <button
                                        onClick={() => setPriceRangeId(null)}
                                        className={`${styles["chip"]} ${priceRangeId === null ? styles["chip-active"] : ""}`}
                                    >
                                        Qualquer
                                    </button>
                                    {PRICE_RANGES.map((range) => (
                                        <button
                                            key={range.id}
                                            onClick={() => setPriceRangeId(range.id)}
                                            className={`${styles["chip"]} ${priceRangeId === range.id ? styles["chip-active"] : ""}`}
                                        >
                                            {range.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className={styles["filter-group"]}>
                                <span className={styles["filter-group-label"]}>Comodidades</span>
                                <div className={styles["chip-row"]}>
                                    {AMENITIES_OPTIONS.map((opt) => (
                                        <button
                                            key={opt.id}
                                            onClick={() => toggleAmenity(opt.id)}
                                            className={`${styles["chip"]} ${amenities.includes(opt.id) ? styles["chip-active"] : ""}`}
                                        >
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {activeFilterCount > 0 && (
                                <button onClick={clearAllFilters} className={styles["clear-filters-btn"]}>
                                    Limpar filtros
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </header>

            <main className={styles["inner"]}>
                <div className={styles["results-head"]}>
                    <p className={styles["results-count"]}><strong>{companies.length}</strong> arenas encontradas</p>
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
                                        <p className={styles["court-place"]}>
                                            <MapPin width={12} height={12} /> {[company.neighborhood, company.city].filter(Boolean).join(", ")}
                                        </p>
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
                            <button onClick={() => { setSearch(""); setActiveSportId(null); clearAllFilters(); }}>Limpar filtros</button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default Courts;
