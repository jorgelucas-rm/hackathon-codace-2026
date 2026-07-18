import { useState } from "react";
import { ChevronLeft, MapPin, Calendar, Clock, Shield, Users, CheckCircle, Sunrise, Sun, Moon, Trophy, Timer } from "lucide-react";
import { Screen } from "../../types";
import { getDays, getTimeSlots, TimeSlot } from "../../services/courts.service";
import styles from "./Schedule.module.scss";

interface ScheduleProps {
    onNavigate: (screen: Screen) => void;
}

const PERIODS = {
    manha: { Icon: Sunrise, label: "Manhã" },
    tarde: { Icon: Sun, label: "Tarde" },
    noite: { Icon: Moon, label: "Noite" },
};

export function Schedule({ onNavigate }: ScheduleProps) {
    const [selectedDay, setSelectedDay] = useState(0);
    const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
    const [reservationType, setReservationType] = useState<"private" | "group">("private");

    const days = getDays();
    const timeSlots = getTimeSlots();
    const allSlots = [...timeSlots.manha, ...timeSlots.tarde, ...timeSlots.noite];
    const selectedSlotData = selectedSlot ? allSlots.find((s) => s.time === selectedSlot) : null;
    const price = selectedSlotData?.price ?? "—";
    const duration = selectedSlotData?.duration ?? "1h";
    const total = selectedSlotData ? `R$ ${parseInt(selectedSlotData.price.replace(/\D/g, ""), 10) + 12},00` : "—";

    const slotClass = (slot: TimeSlot, isSelected: boolean) => {
        if (isSelected) return styles["slot-selected"];
        if (slot.status === "reservado" || slot.status === "indisponivel") return styles["slot-busy"];
        if (slot.status === "ultimas") return styles["slot-last"];
        return styles["slot-free"];
    };

    const reservationTypes = [
        { key: "private" as const, Icon: Shield, title: "Privada", desc: "Você e seus amigos" },
        { key: "group" as const, Icon: Users, title: "Grupo aberto", desc: "Divida o custo" },
    ];

    return (
        <div className={styles["container"]}>
            <div className={styles["main"]}>
                {/* ---------- Header compacto ---------- */}
                <header className={styles["header"]}>
                    <button onClick={() => onNavigate("courtDetail")} className={styles["back"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <div>
                        <span className={styles["eyebrow"]}>Reservar</span>
                        <h1>Escolher horário</h1>
                    </div>
                </header>

                <div className={styles["content"]}>
                    {/* ---------- Resumo da quadra (compacto) ---------- */}
                    <div className={styles["court-summary"]}>
                        <div className={styles["court-thumb"]} style={{ background: "linear-gradient(135deg, rgba(173,153,0,0.2), #E8D7BD)" }}>
                            <Trophy width={22} height={22} />
                        </div>
                        <div className={styles["court-info"]}>
                            <p className={styles["court-name"]}>Arena Beira-Mar</p>
                            <p className={styles["court-place"]}><MapPin width={12} height={12} /> Meireles, Fortaleza</p>
                            <span className={styles["court-sport"]}>Beach Tennis</span>
                        </div>
                        <div className={styles["court-price"]}>
                            <span className={styles["eyebrow"]}>Por hora</span>
                            <strong>R$ 90</strong>
                        </div>
                    </div>

                    {/* ---------- Data ---------- */}
                    <section className={styles["block"]}>
                        <p className={styles["block-label"]}>Escolha o dia</p>
                        <div className={`scrollbar-none ${styles["days"]}`}>
                            {days.map((day, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedDay(i)}
                                    className={`${styles["day"]} ${selectedDay === i ? styles["day-active"] : ""}`}
                                >
                                    <span>{day.label}</span>
                                    <strong>{day.date}</strong>
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* ---------- Tipo de reserva ---------- */}
                    <section className={styles["block"]}>
                        <p className={styles["block-label"]}>Tipo de reserva</p>
                        <div className={styles["types"]}>
                            {reservationTypes.map((opt) => (
                                <button
                                    key={opt.key}
                                    onClick={() => setReservationType(opt.key)}
                                    className={`${styles["type"]} ${reservationType === opt.key ? styles["type-active"] : ""}`}
                                >
                                    <opt.Icon width={18} height={18} />
                                    <span className={styles["type-title"]}>{opt.title}</span>
                                    <span className={styles["type-desc"]}>{opt.desc}</span>
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* ---------- Horários ---------- */}
                    {(["manha", "tarde", "noite"] as const).map((period) => {
                        const PeriodIcon = PERIODS[period].Icon;
                        return (
                            <section key={period} className={styles["block"]}>
                                <p className={styles["block-label"]}><PeriodIcon width={14} height={14} /> {PERIODS[period].label}</p>
                                <div className={styles["slots"]}>
                                    {timeSlots[period].map((slot) => {
                                        const isSelected = selectedSlot === slot.time;
                                        const disabled = slot.status === "reservado" || slot.status === "indisponivel";
                                        return (
                                            <button
                                                key={slot.time}
                                                onClick={() => !disabled && setSelectedSlot(isSelected ? null : slot.time)}
                                                disabled={disabled}
                                                className={`${styles["slot"]} ${slotClass(slot, isSelected)}`}
                                            >
                                                <div className={styles["slot-head"]}>
                                                    <strong>{slot.time}</strong>
                                                    {isSelected && <CheckCircle width={16} height={16} />}
                                                </div>
                                                <span className={styles["slot-price"]}>{slot.price}</span>
                                                {slot.status === "ultimas" && !isSelected && <em className={styles["tag-last"]}>Últimas</em>}
                                                {slot.status === "reservado" && <em className={styles["tag-busy"]}>Reservado</em>}
                                            </button>
                                        );
                                    })}
                                </div>
                            </section>
                        );
                    })}

                    <div className={styles["spacer"]} />
                </div>
            </div>

            {/* ---------- Resumo lateral (desktop) ---------- */}
            <aside className={styles["summary"]}>
                <div className={styles["summary-head"]}>
                    <span className={styles["eyebrow"]}>Resumo</span>
                    <h2>Sua reserva</h2>
                </div>
                <div className={styles["summary-body"]}>
                    <div className={styles["summary-row"]}><span><Trophy width={15} height={15} /> Quadra</span><strong>Arena Beira-Mar</strong></div>
                    <div className={styles["summary-row"]}><span><Calendar width={15} height={15} /> Data</span><strong>{days[selectedDay].label}, {days[selectedDay].date} Jul</strong></div>
                    <div className={styles["summary-row"]}><span><Clock width={15} height={15} /> Horário</span><strong>{selectedSlot ?? "—"}</strong></div>
                    <div className={styles["summary-row"]}><span><Timer width={15} height={15} /> Duração</span><strong>{selectedSlot ? duration : "—"}</strong></div>

                    <div className={styles["summary-divider"]} />

                    <div className={styles["summary-line"]}><span>Valor</span><span>{price}</span></div>
                    <div className={styles["summary-line"]}><span>Taxa de serviço</span><span>{selectedSlot ? "R$ 12,00" : "—"}</span></div>
                    <div className={styles["summary-total"]}><span>Total</span><strong>{total}</strong></div>
                </div>
                <div className={styles["summary-foot"]}>
                    <button
                        onClick={() => selectedSlot && onNavigate("checkout")}
                        disabled={!selectedSlot}
                        className={styles["cta"]}
                    >
                        {selectedSlot ? "Continuar reserva" : "Selecione um horário"}
                    </button>
                </div>
            </aside>

            {/* ---------- Barra fixa (mobile) ---------- */}
            <div className={styles["mobile-bar"]}>
                <div className={styles["mobile-info"]}>
                    <span className={styles["mobile-label"]}>{selectedSlot ? `${days[selectedDay].label} · ${selectedSlot}` : "Nenhum horário"}</span>
                    <strong className={styles["mobile-total"]}>{total}</strong>
                </div>
                <button
                    onClick={() => selectedSlot && onNavigate("checkout")}
                    disabled={!selectedSlot}
                    className={styles["cta"]}
                >
                    {selectedSlot ? "Continuar" : "Escolher horário"}
                </button>
            </div>
        </div>
    );
}

export default Schedule;
