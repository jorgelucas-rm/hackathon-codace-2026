import { useState } from "react";
import { ChevronLeft, Heart, MapPin, Trophy, Star, ThumbsUp, Navigation, Car, Wifi, Coffee, Dumbbell, ArrowRight } from "lucide-react";
import { Screen } from "../../types";
import { StarRow } from "../../components/StarRow/StarRow";
import { getCourtById } from "../../services/courts.service";
import styles from "./CourtDetail.module.scss";

interface CourtDetailProps {
    courtId: number;
    onNavigate: (screen: Screen) => void;
}

function amenityIcon(name: string) {
    const lower = name.toLowerCase();
    if (lower.includes("estac")) return <Car width={17} height={17} />;
    if (lower.includes("wi")) return <Wifi width={17} height={17} />;
    if (lower.includes("bar") || lower.includes("lanch")) return <Coffee width={17} height={17} />;
    return <Dumbbell width={17} height={17} />;
}

export function CourtDetail({ courtId, onNavigate }: CourtDetailProps) {
    const court = getCourtById(courtId);
    const [photoSlide, setPhotoSlide] = useState(0);
    const [fav, setFav] = useState(false);
    const [showAllReviews, setShowAllReviews] = useState(false);

    const ratingDist = [
        { label: "5", value: Math.round(court.reviewCount * 0.6) },
        { label: "4", value: Math.round(court.reviewCount * 0.25) },
        { label: "3", value: Math.round(court.reviewCount * 0.1) },
        { label: "2", value: Math.round(court.reviewCount * 0.03) },
        { label: "1", value: Math.round(court.reviewCount * 0.02) },
    ];
    const visibleReviews = showAllReviews ? court.reviews : court.reviews.slice(0, 2);
    const freeToday = court.todaySlots.filter((s) => s.status === "disponivel" || s.status === "ultimas").length;

    return (
        <div className={styles["container"]}>
            {/* ---------- Capa (contida, não domina) ---------- */}
            <div className={styles["cover"]} style={{ background: court.gradient }}>
                <Trophy width={72} height={72} className={styles["cover-icon"]} />
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
                {court.premium && <span className={styles["cover-premium"]}>PREMIUM</span>}
                <div className={styles["cover-dots"]}>
                    {[0, 1, 2].map((i) => (
                        <button
                            key={i}
                            onClick={() => setPhotoSlide(i)}
                            className={i === photoSlide ? styles["dot-active"] : ""}
                            aria-label={`Foto ${i + 1}`}
                        />
                    ))}
                </div>
            </div>

            <main className={styles["inner"]}>
                {/* ---------- Identidade da quadra (compacta, escaneável) ---------- */}
                <section className={styles["identity"]}>
                    <div className={styles["title-row"]}>
                        <h1>{court.name}</h1>
                        <span className={styles["rating-badge"]}><Star width={14} height={14} /> {court.rating}</span>
                    </div>
                    <div className={styles["meta"]}>
                        <span className={styles["place"]}><MapPin width={13} height={13} /> {court.neighborhood.split(",")[0]}</span>
                        <span className={styles["dot"]} />
                        <span className={styles["distance"]}><Navigation width={12} height={12} /> {court.distance}</span>
                        <span className={styles["dot"]} />
                        <span className={styles["reviews-count"]}>{court.reviewCount} avaliações</span>
                    </div>
                    <div className={styles["tags"]}>
                        {court.sportTags.map((tag) => <span key={tag} className={styles["tag"]}>{tag}</span>)}
                    </div>
                    <p className={styles["desc"]}>{court.desc}</p>
                </section>

                {/* ---------- Horários hoje (caminho principal p/ reserva) ---------- */}
                <section className={styles["section"]}>
                    <div className={styles["section-head"]}>
                        <div>
                            <span className={styles["eyebrow"]}>Disponibilidade</span>
                            <h3>Horários de hoje</h3>
                        </div>
                        <span className={styles["free-pill"]}>{freeToday} livres</span>
                    </div>
                    <div className={styles["slots"]}>
                        {court.todaySlots.map((slot) => {
                            const isDisabled = slot.status === "reservado" || slot.status === "privada";
                            return (
                                <button
                                    key={slot.time}
                                    onClick={() => !isDisabled && onNavigate("schedule")}
                                    disabled={isDisabled}
                                    className={`${styles["slot"]} ${isDisabled ? styles["slot-busy"] : slot.status === "ultimas" ? styles["slot-last"] : styles["slot-free"]}`}
                                >
                                    <strong>{slot.time}</strong>
                                    <span>{isDisabled ? "ocupado" : `${slot.spots} vaga${slot.spots !== 1 ? "s" : ""}`}</span>
                                </button>
                            );
                        })}
                    </div>
                    <button onClick={() => onNavigate("schedule")} className={styles["all-slots"]}>
                        Ver agenda completa <ArrowRight width={15} height={15} />
                    </button>
                </section>

                {/* ---------- Estrutura / comodidades ---------- */}
                <section className={styles["section"]}>
                    <span className={styles["eyebrow"]}>O que oferece</span>
                    <h3>Estrutura</h3>
                    <div className={styles["amenities"]}>
                        {court.amenities.map((a) => (
                            <div key={a} className={styles["amenity"]}>
                                <span className={styles["amenity-icon"]}>{amenityIcon(a)}</span>
                                <span className={styles["amenity-label"]}>{a}</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ---------- Localização (compacta) ---------- */}
                <section className={styles["section"]}>
                    <span className={styles["eyebrow"]}>Onde fica</span>
                    <h3>Localização</h3>
                    <div className={styles["loc-card"]}>
                        <div className={styles["loc-map"]}><MapPin width={26} height={26} /></div>
                        <div className={styles["loc-info"]}>
                            <p className={styles["loc-name"]}>{court.neighborhood}</p>
                            <span className={styles["loc-addr"]}>{court.address}</span>
                            <span className={styles["loc-dist"]}><Navigation width={12} height={12} /> {court.distance} de você</span>
                        </div>
                    </div>
                </section>

                {/* ---------- Avaliações ---------- */}
                <section className={styles["section"]}>
                    <span className={styles["eyebrow"]}>Reputação</span>
                    <h3>Avaliações</h3>
                    <div className={styles["rating-summary"]}>
                        <div className={styles["rating-score"]}>
                            <p>{court.rating}</p>
                            <StarRow rating={Math.round(court.rating)} size="md" />
                            <span>{court.reviewCount} avaliações</span>
                        </div>
                        <div className={styles["rating-bars"]}>
                            {ratingDist.map((row) => (
                                <div key={row.label} className={styles["rating-bar"]}>
                                    <span>{row.label}</span>
                                    <div className={styles["bar-track"]}>
                                        <div style={{ width: `${Math.round((row.value / court.reviewCount) * 100)}%` }} />
                                    </div>
                                    <span className={styles["bar-value"]}>{row.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className={styles["reviews"]}>
                        {visibleReviews.map((review, i) => (
                            <div key={i} className={styles["review"]}>
                                <div className={styles["review-head"]}>
                                    <div className={styles["review-avatar"]}>{review.initials}</div>
                                    <div className={styles["review-id"]}>
                                        <p>{review.name}</p>
                                        <StarRow rating={review.rating} />
                                    </div>
                                    <span>{review.date}</span>
                                </div>
                                <p className={styles["review-text"]}>"{review.text}"</p>
                                <button className={styles["review-useful"]}><ThumbsUp width={12} height={12} /> Útil</button>
                            </div>
                        ))}
                    </div>
                    {court.reviews.length > 2 && (
                        <button onClick={() => setShowAllReviews(!showAllReviews)} className={styles["more-reviews"]}>
                            {showAllReviews ? "Ver menos" : `Ver todas as ${court.reviews.length} avaliações`}
                        </button>
                    )}
                </section>
            </main>

            {/* ---------- CTA fixo ---------- */}
            <div className={styles["cta-bar"]}>
                <div className={styles["cta-inner"]}>
                    <div className={styles["cta-price"]}>
                        <span>A partir de</span>
                        <strong>{court.price}</strong>
                    </div>
                    <button onClick={() => onNavigate("schedule")} className={styles["cta-btn"]}>
                        Escolher horário <ArrowRight width={18} height={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CourtDetail;
