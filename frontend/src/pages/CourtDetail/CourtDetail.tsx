import { useState } from "react";
import { ChevronLeft, Heart, MapPin, Trophy, Star, ThumbsUp, Car, Wifi, Coffee, Dumbbell, ArrowRight, Loader2 } from "lucide-react";
import { Screen } from "../../types";
import { StarRow } from "../../components/StarRow/StarRow";
import { formatPriceCents } from "../../services/companies.service";
import { useCompanyDetail, useCompanyReviews } from "./hooks/useCourtDetail";
import styles from "./CourtDetail.module.scss";

interface CourtDetailProps {
    courtId: number;
    onNavigate: (screen: Screen) => void;
    onSelectSchedule: (courtId: number) => void;
}

function amenityIcon(name: string) {
    const lower = name.toLowerCase();
    if (lower.includes("estac")) return <Car width={17} height={17} />;
    if (lower.includes("wi")) return <Wifi width={17} height={17} />;
    if (lower.includes("bar") || lower.includes("lanch")) return <Coffee width={17} height={17} />;
    return <Dumbbell width={17} height={17} />;
}

function initialsOf(name: string | null): string {
    if (!name) return "?";
    const parts = name.trim().split(/\s+/);
    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
    return (first + last).toUpperCase();
}

export function CourtDetail({ courtId, onNavigate, onSelectSchedule }: CourtDetailProps) {
    const { data: company, isLoading, isError } = useCompanyDetail(courtId);
    const { data: reviewsPage } = useCompanyReviews(courtId);
    const [photoSlide, setPhotoSlide] = useState(0);
    const [fav, setFav] = useState(false);
    const [showAllReviews, setShowAllReviews] = useState(false);

    if (isLoading) {
        return (
            <div className={styles["container"]}>
                <div className={styles["inner"]} style={{ padding: "64px 0", textAlign: "center" }}>
                    <Loader2 width={36} height={36} />
                    <p>Carregando arena...</p>
                </div>
            </div>
        );
    }

    if (isError || !company) {
        return (
            <div className={styles["container"]}>
                <div className={styles["inner"]} style={{ padding: "64px 0", textAlign: "center" }}>
                    <p>Não foi possível carregar essa arena.</p>
                    <button onClick={() => onNavigate("courts")}>Voltar</button>
                </div>
            </div>
        );
    }

    const reviews = reviewsPage?.items ?? [];
    const visibleReviews = showAllReviews ? reviews : reviews.slice(0, 2);
    const ratingCounts = [5, 4, 3, 2, 1].map((star) => ({
        label: String(star),
        value: reviews.filter((r) => r.rating === star).length,
    }));

    const sportTags = Array.from(
        new Set(company.courts.flatMap((c) => c.sports.map((s) => s.name)))
    );
    const activeCourts = company.courts.filter((c) => c.status === "ACTIVE");
    const cheapestActiveCourt = activeCourts.length
        ? activeCourts.reduce((min, c) => (c.base_price_hour < min.base_price_hour ? c : min))
        : null;
    const cheapestCourt = cheapestActiveCourt?.base_price_hour ?? null;
    const defaultScheduleCourtId = cheapestActiveCourt?.id ?? company.courts[0]?.id ?? null;
    const coverPhoto = company.photos[photoSlide] ?? company.photos[0] ?? null;
    const addressLine = `${company.street}, ${company.number} · ${company.neighborhood}`;

    return (
        <div className={styles["container"]}>
            {/* ---------- Capa (contida, não domina) ---------- */}
            <div
                className={styles["cover"]}
                style={coverPhoto
                    ? { backgroundImage: `url(${coverPhoto})`, backgroundSize: "cover", backgroundPosition: "center" }
                    : { background: "linear-gradient(135deg, rgba(173,153,0,0.2), #E8D7BD)" }}
            >
                {!coverPhoto && <Trophy width={72} height={72} className={styles["cover-icon"]} />}
                <div className={styles["cover-fade"]} />
                <button onClick={() => onNavigate("courts")} className={styles["cover-btn"]} style={{ left: 16 }} aria-label="Voltar">
                    <ChevronLeft width={20} height={20} />
                </button>
                <button
                    onClick={() => setFav(!fav)}
                    className={`${styles["cover-btn"]} ${fav ? styles["fav-active"] : ""}`}
                    style={{ right: 16 }}
                    aria-label="Favoritar"
                >
                    <Heart width={20} height={20} />
                </button>
                {company.photos.length > 1 && (
                    <div className={styles["cover-dots"]}>
                        {company.photos.slice(0, 3).map((_, i) => (
                            <button
                                key={i}
                                onClick={() => setPhotoSlide(i)}
                                className={i === photoSlide ? styles["dot-active"] : ""}
                                aria-label={`Foto ${i + 1}`}
                            />
                        ))}
                    </div>
                )}
            </div>

            <main className={styles["inner"]}>
                {/* ---------- Identidade da arena (compacta, escaneável) ---------- */}
                <section className={styles["identity"]}>
                    <div className={styles["title-row"]}>
                        <h1>{company.name}</h1>
                        <span className={styles["rating-badge"]}>
                            <Star width={14} height={14} />
                            {company.nota_media !== null ? company.nota_media.toFixed(1) : "novo"}
                        </span>
                    </div>
                    <div className={styles["meta"]}>
                        <span className={styles["place"]}><MapPin width={13} height={13} /> {company.neighborhood}, {company.city}</span>
                        <span className={styles["dot"]} />
                        <span className={styles["reviews-count"]}>{reviewsPage?.total_filtered ?? 0} avaliações</span>
                    </div>
                    <div className={styles["tags"]}>
                        {sportTags.map((tag) => <span key={tag} className={styles["tag"]}>{tag}</span>)}
                    </div>
                    {company.description && <p className={styles["desc"]}>{company.description}</p>}
                </section>

                {/* ---------- Quadras da arena ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["section-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Estrutura</span>
                            <h3>Quadras</h3>
                        </div>
                        <span className={styles["free-pill"]}>{activeCourts.length} ativas</span>
                    </div>
                    <div className={styles["slots"]}>
                        {company.courts.map((court) => (
                            <button
                                key={court.id}
                                onClick={() => onSelectSchedule(court.id)}
                                className={`${styles["slot"]} ${styles["slot-free"]}`}
                            >
                                <strong>{court.name}</strong>
                                <span>{court.sports.map((s) => s.name).join(", ") || "—"} · {formatPriceCents(court.base_price_hour)}/h</span>
                            </button>
                        ))}
                    </div>
                    {defaultScheduleCourtId !== null && (
                        <button onClick={() => onSelectSchedule(defaultScheduleCourtId)} className={styles["all-slots"]}>
                            Ver agenda completa <ArrowRight width={15} height={15} />
                        </button>
                    )}
                </section>

                {/* ---------- Comodidades ---------- */}
                {company.amenities.length > 0 && (
                    <section className={styles["section"]}>
                        <span className={styles["eyebrow"]}>O que oferece</span>
                        <h3>Comodidades</h3>
                        <div className={styles["amenities"]}>
                            {company.amenities.map((a) => (
                                <div key={a} className={styles["amenity"]}>
                                    <span className={styles["amenity-icon"]}>{amenityIcon(a)}</span>
                                    <span className={styles["amenity-label"]}>{a}</span>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* ---------- Localização (compacta) ---------- */}
                <section className={styles["section"]}>
                    <span className={styles["eyebrow"]}>Onde fica</span>
                    <h3>Localização</h3>
                    <div className={styles["loc-card"]}>
                        <div className={styles["loc-map"]}><MapPin width={26} height={26} /></div>
                        <div className={styles["loc-info"]}>
                            <p className={styles["loc-name"]}>{company.neighborhood}</p>
                            <span className={styles["loc-addr"]}>{addressLine}</span>
                        </div>
                    </div>
                </section>

                {/* ---------- Avaliações ---------- */}
                <section className={styles["section"]}>
                    <span className={styles["eyebrow"]}>Reputação</span>
                    <h3>Avaliações</h3>
                    <div className={styles["rating-summary"]}>
                        <div className={styles["rating-score"]}>
                            <p>{company.nota_media !== null ? company.nota_media.toFixed(1) : "—"}</p>
                            <StarRow rating={Math.round(company.nota_media ?? 0)} size="md" />
                            <span>{reviewsPage?.total_filtered ?? 0} avaliações</span>
                        </div>
                        {reviews.length > 0 && (
                            <div className={styles["rating-bars"]}>
                                {ratingCounts.map((row) => (
                                    <div key={row.label} className={styles["rating-bar"]}>
                                        <span>{row.label}</span>
                                        <div className={styles["bar-track"]}>
                                            <div style={{ width: `${Math.round((row.value / reviews.length) * 100)}%` }} />
                                        </div>
                                        <span className={styles["bar-value"]}>{row.value}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                    {reviews.length === 0 ? (
                        <p className={styles["desc"]}>Essa arena ainda não tem avaliações.</p>
                    ) : (
                        <>
                            <div className={styles["reviews"]}>
                                {visibleReviews.map((review) => (
                                    <div key={review.id} className={styles["review"]}>
                                        <div className={styles["review-head"]}>
                                            <div className={styles["review-avatar"]}>{initialsOf(review.user_name)}</div>
                                            <div className={styles["review-id"]}>
                                                <p>{review.user_name ?? "Jogador"}</p>
                                                <StarRow rating={review.rating} />
                                            </div>
                                            <span>{new Date(review.created_at).toLocaleDateString("pt-BR")}</span>
                                        </div>
                                        {review.comment && <p className={styles["review-text"]}>"{review.comment}"</p>}
                                        <button className={styles["review-useful"]}><ThumbsUp width={12} height={12} /> Útil ({review.helpful_count})</button>
                                    </div>
                                ))}
                            </div>
                            {reviews.length > 2 && (
                                <button onClick={() => setShowAllReviews(!showAllReviews)} className={styles["more-reviews"]}>
                                    {showAllReviews ? "Ver menos" : `Ver todas as ${reviews.length} avaliações`}
                                </button>
                            )}
                        </>
                    )}
                </section>
            </main>

            {/* ---------- CTA fixo ---------- */}
            <div className={styles["cta-bar"]}>
                <div className={styles["cta-inner"]}>
                    <div className={styles["cta-price"]}>
                        <span>A partir de</span>
                        <strong>{formatPriceCents(cheapestCourt)}</strong>
                    </div>
                    <button
                        onClick={() => defaultScheduleCourtId !== null && onSelectSchedule(defaultScheduleCourtId)}
                        disabled={defaultScheduleCourtId === null}
                        className={styles["cta-btn"]}
                    >
                        Escolher horário <ArrowRight width={18} height={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CourtDetail;
