import { Home, Search, Users, User } from "lucide-react";
import { Screen } from "../../types";
import styles from "./BottomNav.module.scss";

interface BottomNavProps {
    active: Screen;
    onNavigate: (screen: Screen) => void;
}

const TABS = [
    { screen: "home" as Screen, Icon: Home, label: "Início" },
    { screen: "courts" as Screen, Icon: Search, label: "Quadras" },
    { screen: "match" as Screen, Icon: Users, label: "Partidas" },
    { screen: "profile" as Screen, Icon: User, label: "Perfil" },
];

export function BottomNav({ active, onNavigate }: BottomNavProps) {
    const inCourts = ["courts", "courtDetail", "schedule"].includes(active);

    return (
        <nav className={styles["nav"]}>
            {TABS.map((tab) => {
                const isActive = active === tab.screen || (tab.screen === "courts" && inCourts);
                return (
                    <button
                        key={tab.screen}
                        onClick={() => onNavigate(tab.screen)}
                        className={`${styles["tab"]} ${isActive ? styles["active"] : ""}`}
                    >
                        <tab.Icon width={20} height={20} />
                        <span>{tab.label}</span>
                        {isActive && <span className={styles["indicator"]} />}
                    </button>
                );
            })}
        </nav>
    );
}

export default BottomNav;
