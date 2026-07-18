import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, Loader2, CircleDot, Activity, Volleyball, Waves, Dumbbell, CalendarClock, Users } from "lucide-react";
import { Screen } from "../../types";
import { BookingRead, formatHHMM, formatPriceCents } from "../../services/booking.service";
import { useMyBookings } from "./hooks/useBookings";
import { useMyGroups } from "../../hooks/useGroups";
import { BookingDetailModal } from "./BookingDetailModal";
import { JoinGroupModal } from "../../components/JoinGroupModal/JoinGroupModal";
import styles from "./Match.module.scss";

interface MatchProps {
    onNavigate: (screen: Screen) => void;
}

type ApptTab = "proximos" | "concluidos" | "cancelados" | "grupos";

const APPT_TABS: { key: ApptTab; label: string }[] = [
    { key: "proximos", label: "Próximos" },
    { key: "grupos", label: "Meus grupos" },
    { key: "concluidos", label: "Concluídos" },
    { key: "cancelados", label: "Cancelados" },
];

const GROUP_STATUS_LABEL: Record<string, string> = {
    OPEN: "Aguardando vagas",
    FULL: "Lotado",
    CONFIRMED: "Confirmado",
    CANCELED: "Cancelado",
};

const GROUP_STATUS_BADGE: Record<string, "upcoming" | "done" | "cancel"> = {
    OPEN: "upcoming",
    FULL: "upcoming",
    CONFIRMED: "done",
    CANCELED: "cancel",
};

const SPORT_ICON: Record<string, typeof CircleDot> = {
    "Futebol": CircleDot,
    "Futebol Society": CircleDot,
    "Futsal": Activity,
    "Vôlei": Volleyball,
    "Vôlei de Praia": Volleyball,
    "Beach Tennis": Waves,
    "Basquete": Dumbbell,
};

const STATUS_LABEL: Record<string, string> = {
    PENDING: "Pendente",
    CONFIRMED: "Confirmado",
    COMPLETED: "Concluído",
    CANCELED: "Cancelado",
    BLOCKED: "Bloqueado",
};

const STATUS_BADGE: Record<string, "upcoming" | "done" | "cancel"> = {
    PENDING: "upcoming",
    CONFIRMED: "upcoming",
    COMPLETED: "done",
    CANCELED: "cancel",
    BLOCKED: "cancel",
};

const badgeClass = { upcoming: "badge-upcoming", done: "badge-done", cancel: "badge-cancel" };

function iconFor(booking: BookingRead) {
    return SPORT_ICON[booking.sport_names[0] ?? ""] ?? CalendarClock;
}

function formatShortDate(date: string): string {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

export function Match({ onNavigate }: MatchProps) {
    const [searchParams, setSearchParams] = useSearchParams();
    const initialBookingId = searchParams.get("bookingId");
    const initialGroupId = searchParams.get("groupId");
    const [apptTab, setApptTab] = useState<ApptTab>(initialGroupId ? "grupos" : "proximos");
    const [selectedBookingId, setSelectedBookingId] = useState<number | null>(
        initialBookingId ? Number(initialBookingId) : null
    );
    const [selectedGroupId, setSelectedGroupId] = useState<number | null>(
        initialGroupId ? Number(initialGroupId) : null
    );

    const upcoming = useMyBookings("upcoming");
    const history = useMyBookings("history");
    const myGroups = useMyGroups();

    const isLoading = apptTab === "grupos" ? myGroups.isLoading : apptTab === "proximos" ? upcoming.isLoading : history.isLoading;
    const isError = apptTab === "grupos" ? myGroups.isError : apptTab === "proximos" ? upcoming.isError : history.isError;

    const appointments = useMemo(() => {
        if (apptTab === "proximos") return upcoming.data ?? [];
        if (apptTab === "concluidos") return (history.data ?? []).filter((b) => b.status === "COMPLETED");
        if (apptTab === "cancelados") return (history.data ?? []).filter((b) => b.status === "CANCELED");
        return [];
    }, [apptTab, upcoming.data, history.data]);

    const groups = myGroups.data ?? [];

    return (
        <div className={styles["container"]}>
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <button onClick={() => onNavigate("home")} className={styles["back"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <span className={styles["header-label"]}>Reservas</span>
                </div>
            </header>

            <main className={styles["inner"]}>
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

                    {isLoading && (
                        <div className={styles["appt-loading"]}>
                            <Loader2 width={20} height={20} className={styles["spin"]} />
                            <span>Carregando{apptTab === "grupos" ? " seus grupos" : " suas reservas"}...</span>
                        </div>
                    )}

                    {isError && !isLoading && (
                        <p className={styles["appt-empty"]}>
                            Não foi possível carregar {apptTab === "grupos" ? "seus grupos" : "suas reservas"} agora.
                        </p>
                    )}

                    {!isLoading && !isError && apptTab === "grupos" && (
                        <div className={styles["appt-list"]}>
                            {groups.length > 0 ? groups.map((g) => {
                                const kind = GROUP_STATUS_BADGE[g.status] ?? "upcoming";
                                return (
                                    <button
                                        key={g.id}
                                        className={styles["appt-card"]}
                                        onClick={() => setSelectedGroupId(g.id)}
                                    >
                                        <span className={styles["appt-icon"]}><Users width={20} height={20} /></span>
                                        <div className={styles["appt-info"]}>
                                            <p className={styles["appt-name"]}>{g.court_name ?? "Partida em grupo"}</p>
                                            {g.company_name && <p className={styles["appt-place"]}>{g.company_name}</p>}
                                            <p className={styles["appt-sub"]}>
                                                {formatShortDate(g.date)} · {formatHHMM(g.start_time)} · {g.filled_spots}/{g.total_spots} vagas · {formatPriceCents(g.spot_price)}
                                            </p>
                                        </div>
                                        <span className={`${styles["badge"]} ${styles[badgeClass[kind]]}`}>{GROUP_STATUS_LABEL[g.status] ?? g.status}</span>
                                    </button>
                                );
                            }) : (
                                <p className={styles["appt-empty"]}>Você ainda não participa de nenhum grupo.</p>
                            )}
                        </div>
                    )}

                    {!isLoading && !isError && apptTab !== "grupos" && (
                        <div className={styles["appt-list"]}>
                            {appointments.length > 0 ? appointments.map((b) => {
                                const Icon = iconFor(b);
                                const kind = STATUS_BADGE[b.status] ?? "upcoming";
                                return (
                                    <button
                                        key={b.id}
                                        className={styles["appt-card"]}
                                        onClick={() => setSelectedBookingId(b.id)}
                                    >
                                        <span className={styles["appt-icon"]}><Icon width={20} height={20} /></span>
                                        <div className={styles["appt-info"]}>
                                            <p className={styles["appt-name"]}>{b.court_name ?? "Reserva"}</p>
                                            {b.company_name && <p className={styles["appt-place"]}>{b.company_name}</p>}
                                            <p className={styles["appt-sub"]}>
                                                {formatShortDate(b.date)} · {formatHHMM(b.start_time)} · {formatPriceCents(b.type === "GROUP" ? b.group?.spot_price ?? b.total_price : b.total_price)}
                                            </p>
                                        </div>
                                        <span className={`${styles["badge"]} ${styles[badgeClass[kind]]}`}>{STATUS_LABEL[b.status] ?? b.status}</span>
                                    </button>
                                );
                            }) : (
                                <p className={styles["appt-empty"]}>Nenhuma partida nesta categoria.</p>
                            )}
                        </div>
                    )}
                </section>
            </main>

            <BookingDetailModal
                bookingId={selectedBookingId}
                onClose={() => {
                    setSelectedBookingId(null);
                    if (searchParams.has("bookingId")) setSearchParams((p) => { p.delete("bookingId"); return p; });
                }}
            />
            <JoinGroupModal
                groupId={selectedGroupId}
                mode="manage"
                onClose={() => setSelectedGroupId(null)}
                onJoined={() => setSelectedGroupId(null)}
            />
        </div>
    );
}

export default Match;
