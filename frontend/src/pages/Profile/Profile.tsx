import { useState } from "react";
import {
    MapPin, ChevronRight, LogOut, User, Calendar, Heart,
} from "lucide-react";
import { Screen } from "../../types";
import { ConfirmModal } from "../../components/ConfirmModal/ConfirmModal";
import { useMe } from "../../hooks/useMe";
import { useAuth } from "../../contexts/AuthContext";
import { useMyBookings } from "../Match/hooks/useBookings";
import { useMyGroups } from "../../hooks/useGroups";
import styles from "./Profile.module.scss";

interface ProfileProps {
    onNavigate: (screen: Screen) => void;
}

const SKILL_LABELS: Record<string, string> = {
    BEGINNER: "Iniciante",
    INTERMEDIATE: "Intermediário",
    ADVANCED: "Avançado",
};

const MENU: { Icon: typeof User; title: string; desc: string; target: Screen }[] = [
    { Icon: User, title: "Minha Conta", desc: "Meus dados pessoais", target: "account" },
    { Icon: Calendar, title: "Minhas Reservas", desc: "Histórico e próximas reservas", target: "match" },
    { Icon: Heart, title: "Favoritos", desc: "Quadras e esportes favoritos", target: "courts" },
];

export function Profile({ onNavigate }: ProfileProps) {
    const [showLogoutModal, setShowLogoutModal] = useState(false);
    const { data: me } = useMe();
    const { logout } = useAuth();
    const { data: upcomingBookings } = useMyBookings("upcoming");
    const { data: historyBookings } = useMyBookings("history");
    const { data: myGroups } = useMyGroups();

    const user = me?.entity;

    // Estatísticas reais — nada mockado: contagens vêm de reservas/grupos do
    // próprio usuário e do perfil (esportes de interesse, quadras favoritas).
    const STATS = [
        { v: String((upcomingBookings?.length ?? 0) + (historyBookings?.length ?? 0)), l: "Reservas" },
        { v: String(myGroups?.length ?? 0), l: "Partidas" },
        { v: String(user?.sports_of_interest.length ?? 0), l: "Esportes" },
        { v: String(user?.favorite_courts.length ?? 0), l: "Favoritos" },
    ];

    return (
        <div className={styles["container"]}>
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <span className={styles["eyebrow"]}>Perfil do jogador</span>
                </div>
            </header>

            <main className={styles["inner"]}>
                <div className={styles["grid"]}>
                    {/* ---------- Identidade (principal) ---------- */}
                    <section className={styles["identity-card"]}>
                        <div className={styles["avatar"]}>
                            {user?.avatar ? <img src={user.avatar} alt="Avatar" /> : <User width={40} height={40} />}
                        </div>
                        <div className={styles["identity-info"]}>
                            <h1 className={styles["name"]}>{user?.name ?? "Carregando..."}</h1>
                            <div className={styles["identity-meta"]}>
                                <span className={styles["level"]}>
                                    {user?.skill_level ? SKILL_LABELS[user.skill_level] ?? user.skill_level : "Nível não definido"}
                                </span>
                                {user?.phone && <span className={styles["place"]}><MapPin width={12} height={12} /> {user.phone}</span>}
                            </div>
                        </div>
                        <button
                            className={`button-secondary ${styles["edit-btn"]}`}
                            onClick={() => onNavigate("account")}
                        >
                            Editar Perfil
                        </button>
                    </section>

                    {/* ---------- Estatísticas (secundário) ---------- */}
                    <section className={styles["stats"]}>
                        {STATS.map((s) => (
                            <div key={s.l} className={styles["stat"]}>
                                <p>{s.v}</p>
                                <span>{s.l}</span>
                            </div>
                        ))}
                    </section>

                    {/* ---------- Menu / navegação ---------- */}
                    <nav className={styles["menu-card"]}>
                        {MENU.map((item) => (
                            <button key={item.title} className={styles["menu-item"]} onClick={() => onNavigate(item.target)}>
                                <div className="icon-box"><item.Icon width={20} height={20} /></div>
                                <div className={styles["menu-text"]}>
                                    <p>{item.title}</p>
                                    <span>{item.desc}</span>
                                </div>
                                <ChevronRight width={16} height={16} className={styles["menu-chevron"]} />
                            </button>
                        ))}
                    </nav>

                    {/* ---------- Ação destrutiva (subordinada) ---------- */}
                    <div className={styles["logout-wrap"]}>
                        <button onClick={() => setShowLogoutModal(true)} className={styles["logout"]}>
                            <LogOut width={18} height={18} /> Sair da Conta
                        </button>
                    </div>
                </div>
            </main>

            <ConfirmModal
                open={showLogoutModal}
                icon={<LogOut width={24} height={24} />}
                title="Sair da conta?"
                message="Você precisará entrar novamente para acessar suas reservas e partidas."
                confirmLabel="Confirmar saída"
                cancelLabel="Cancelar"
                danger
                onCancel={() => setShowLogoutModal(false)}
                onConfirm={() => { setShowLogoutModal(false); logout(); onNavigate("login"); }}
            />
        </div>
    );
}

export default Profile;
