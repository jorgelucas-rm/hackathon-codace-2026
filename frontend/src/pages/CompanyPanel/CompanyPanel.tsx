import { AlertCircle, BarChart3, Building2, CalendarDays, LayoutGrid, MapPin, User } from "lucide-react";
import { useMyCompany } from "./hooks/useCompanyPanel";
import AgendaTab from "./tabs/AgendaTab";
import CourtsTab from "./tabs/CourtsTab";
import ReportTab from "./tabs/ReportTab";
import ProfileTab from "./tabs/ProfileTab";
import styles from "./CompanyPanel.module.scss";

export type PanelTab = "agenda" | "quadras" | "relatorio" | "perfil";

export const PANEL_TABS: PanelTab[] = ["agenda", "quadras", "relatorio", "perfil"];

interface CompanyPanelProps {
    tab: PanelTab;
    onChangeTab: (tab: PanelTab) => void;
}

const NAV_ITEMS: { tab: PanelTab; Icon: typeof CalendarDays; label: string }[] = [
    { tab: "agenda", Icon: CalendarDays, label: "Agenda" },
    { tab: "quadras", Icon: LayoutGrid, label: "Quadras" },
    { tab: "relatorio", Icon: BarChart3, label: "Relatório" },
    { tab: "perfil", Icon: User, label: "Perfil" },
];

export function CompanyPanel({ tab, onChangeTab }: CompanyPanelProps) {
    const { data: company } = useMyCompany();

    const location = company
        ? [company.neighborhood, company.city].filter(Boolean).join(", ")
        : "";
    const showBanner = !!company && (company.opening_hours?.length ?? 0) === 0 && tab !== "perfil";

    return (
        <div className={styles["container"]}>
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <div className={styles["header-row"]}>
                        <div>
                            <div className={styles["location"]}>
                                <MapPin width={14} height={14} />
                                {location || "—"}
                            </div>
                            <div className={styles["arena-name"]}>{company?.name ?? "Carregando..."}</div>
                        </div>
                        <div className={styles["avatar"]}>
                            <Building2 width={20} height={20} />
                        </div>
                    </div>
                </div>
            </header>

            <div className={styles["content"]}>
                {showBanner && (
                    <div className={styles["banner"]}>
                        <div className={styles["banner-icon"]}>
                            <AlertCircle width={20} height={20} />
                        </div>
                        <div className={styles["banner-text"]}>
                            <strong>Complete o perfil da arena</strong>
                            <span>
                                Sem horário de funcionamento cadastrado, os jogadores não veem horários
                                disponíveis — ninguém consegue reservar.
                            </span>
                        </div>
                        <button className={styles["banner-btn"]} onClick={() => onChangeTab("perfil")}>
                            Completar perfil
                        </button>
                    </div>
                )}

                {tab === "agenda" && <AgendaTab />}
                {tab === "quadras" && <CourtsTab />}
                {tab === "relatorio" && <ReportTab />}
                {tab === "perfil" && <ProfileTab />}
            </div>

            <nav className={styles["nav"]}>
                {NAV_ITEMS.map((item) => {
                    const active = tab === item.tab;
                    return (
                        <button
                            key={item.tab}
                            onClick={() => onChangeTab(item.tab)}
                            className={`${styles["nav-btn"]} ${active ? styles["nav-active"] : ""}`}
                        >
                            <item.Icon width={21} height={21} />
                            <span>{item.label}</span>
                            <i className={active ? styles["nav-indicator"] : styles["nav-indicator-off"]} />
                        </button>
                    );
                })}
            </nav>
        </div>
    );
}

export default CompanyPanel;
