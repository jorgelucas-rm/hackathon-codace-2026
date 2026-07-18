import { useState } from "react";
import {
    MapPin, ChevronRight, LogOut, User, Calendar, Heart,
    CreditCard, Users,
} from "lucide-react";
import { Screen } from "../../types";
import { ConfirmModal } from "../../components/ConfirmModal/ConfirmModal";
import { useMe } from "../../hooks/useMe";
import { useAuth } from "../../contexts/AuthContext";
import styles from "./Profile.module.scss";

interface ProfileProps {
    onNavigate: (screen: Screen) => void;
}

const STATS = [
    { v: "47", l: "Reservas" },
    { v: "132", l: "Partidas" },
    { v: "4.8", l: "Avaliação" },
    { v: "28", l: "Amigos" },
];

const MENU = [
    { Icon: User, title: "Minha Conta", desc: "Meus dados pessoais" },
    { Icon: Calendar, title: "Minhas Reservas", desc: "Histórico e próximas reservas" },
    { Icon: Heart, title: "Favoritos", desc: "Quadras e esportes favoritos" },
    { Icon: CreditCard, title: "Métodos de Pagamento", desc: "Cartões e formas de pagamento" },
    { Icon: Users, title: "Amigos", desc: "Convites e conexões" },
];

export function Profile({ onNavigate }: ProfileProps) {
    const [showLogoutModal, setShowLogoutModal] = useState(false);
    const { data: me } = useMe();
    const { logout } = useAuth();

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
                        <div className={styles["avatar"]}><User width={40} height={40} /></div>
                        <div className={styles["identity-info"]}>
                            <h1 className={styles["name"]}>{me?.entity?.name ?? "Carregando..."}</h1>
                            <div className={styles["identity-meta"]}>
                                <span className={styles["level"]}>{me?.entity?.skill_level ?? "Nível não definido"}</span>
                                <span className={styles["place"]}><MapPin width={12} height={12} /> Fortaleza, CE</span>
                            </div>
                        </div>
                        <button className={`button-secondary ${styles["edit-btn"]}`}>Editar Perfil</button>
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
                            <button key={item.title} className={styles["menu-item"]}>
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
