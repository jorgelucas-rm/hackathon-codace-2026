import { useEffect, useRef, useState } from "react";
import { ChevronLeft, User, Phone, MapPin, Hash, Check, Trophy } from "lucide-react";
import { Screen } from "../../types";
import { Input } from "../../components/inputs/Input";
import { Button } from "../../components/button/Button";
import { useMe } from "../../hooks/useMe";
import { useSports } from "../../hooks/useCompanies";
import { useAvatarPresets, useSetAvatarPreset, useUpdateProfile } from "../../hooks/useAccount";
import { SkillLevel } from "../../services/user.service";
import { getSportIcon } from "../../components/icons/SportIcons";
import styles from "./Account.module.scss";

interface AccountProps {
    onNavigate: (screen: Screen) => void;
}

const SKILL_LEVELS: { key: SkillLevel; label: string }[] = [
    { key: "BEGINNER", label: "Iniciante" },
    { key: "INTERMEDIATE", label: "Intermediário" },
    { key: "ADVANCED", label: "Avançado" },
];

export function Account({ onNavigate }: AccountProps) {
    const { data: me } = useMe();
    const { data: sports } = useSports();
    const { data: avatarPresets } = useAvatarPresets();
    const updateProfile = useUpdateProfile();
    const setAvatarPreset = useSetAvatarPreset();

    const user = me?.entity ?? null;

    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [street, setStreet] = useState("");
    const [number, setNumber] = useState("");
    const [zipCode, setZipCode] = useState("");
    const [skillLevel, setSkillLevel] = useState<SkillLevel | null>(null);
    const [sportsOfInterest, setSportsOfInterest] = useState<number[]>([]);
    const [showAvatarPicker, setShowAvatarPicker] = useState(false);
    const [error, setError] = useState("");
    const [saved, setSaved] = useState(false);
    const initialized = useRef(false);

    // Sincroniza o formulário com os dados reais assim que `useMe()` resolve
    // — só uma vez, pra não sobrescrever o que o usuário já digitou.
    useEffect(() => {
        if (initialized.current || !user) return;
        initialized.current = true;
        setName(user.name);
        setPhone(user.phone ?? "");
        setStreet(user.street ?? "");
        setNumber(user.number ?? "");
        setZipCode(user.zip_code ?? "");
        setSkillLevel((user.skill_level as SkillLevel) ?? null);
        setSportsOfInterest(user.sports_of_interest ?? []);
    }, [user]);

    const toggleSport = (sportId: number) => {
        setSportsOfInterest((prev) =>
            prev.includes(sportId) ? prev.filter((id) => id !== sportId) : [...prev, sportId]
        );
    };

    const handleSave = () => {
        setError("");
        setSaved(false);
        if (!name.trim()) {
            setError("O nome não pode ficar em branco.");
            return;
        }
        updateProfile.mutate(
            {
                name,
                phone: phone || null,
                street: street || null,
                number: number || null,
                zip_code: zipCode || null,
                skill_level: skillLevel,
                sports_of_interest: sportsOfInterest,
            },
            {
                onSuccess: () => setSaved(true),
                onError: (err) => setError(err.message),
            }
        );
    };

    const handlePickPreset = (presetId: string) => {
        setAvatarPreset.mutate(presetId, {
            onSuccess: () => setShowAvatarPicker(false),
            onError: (err) => setError(err.message),
        });
    };

    return (
        <div className={styles["container"]}>
            <header className={styles["header"]}>
                <div className={styles["inner"]}>
                    <button onClick={() => onNavigate("profile")} className={styles["back-btn"]} aria-label="Voltar">
                        <ChevronLeft width={20} height={20} />
                    </button>
                    <span className={styles["eyebrow"]}>Perfil do jogador</span>
                    <h1 className={styles["title"]}>Minha Conta</h1>
                </div>
            </header>

            <main className={styles["inner"]}>
                {/* ---------- Avatar ---------- */}
                <section className={styles["avatar-card"]}>
                    <div className={styles["avatar-preview"]}>
                        {user?.avatar
                            ? <img src={user.avatar} alt="Avatar" />
                            : <User width={36} height={36} />}
                    </div>
                    <div className={styles["avatar-actions"]}>
                        <p className={styles["name-preview"]}>{user?.name ?? "Carregando..."}</p>
                        <button
                            type="button"
                            className="button-secondary"
                            onClick={() => setShowAvatarPicker((v) => !v)}
                        >
                            Alterar foto
                        </button>
                    </div>

                    {showAvatarPicker && (
                        <div className={styles["avatar-picker"]}>
                            <div className={styles["preset-grid"]}>
                                {(avatarPresets ?? []).map((preset) => (
                                    <button
                                        key={preset.id}
                                        type="button"
                                        className={styles["preset-item"]}
                                        onClick={() => handlePickPreset(preset.id)}
                                        disabled={setAvatarPreset.isPending}
                                        aria-label={preset.id}
                                    >
                                        {preset.url && <img src={preset.url} alt={preset.id} />}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </section>

                {/* ---------- Dados pessoais ---------- */}
                <section className={styles["form-card"]}>
                    <h3>Dados pessoais</h3>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Nome</span>
                        <Input value={name} onChange={setName} icon={<User width={18} height={18} />} placeholder="Seu nome" />
                    </div>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>E-mail</span>
                        <Input value={user?.email ?? ""} icon={<User width={18} height={18} />} />
                        <span className={styles["field-hint"]}>O e-mail não pode ser alterado.</span>
                    </div>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Telefone</span>
                        <Input type="tel" value={phone} onChange={setPhone} icon={<Phone width={18} height={18} />} placeholder="(85) 90000-0000" />
                    </div>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Rua</span>
                        <Input value={street} onChange={setStreet} icon={<MapPin width={18} height={18} />} placeholder="Nome da rua" />
                    </div>

                    <div className={styles["address-row"]}>
                        <div className={styles["field-group"]}>
                            <span className={styles["field-label"]}>Número</span>
                            <Input value={number} onChange={setNumber} icon={<Hash width={18} height={18} />} placeholder="123" />
                        </div>

                        <div className={styles["field-group"]}>
                            <span className={styles["field-label"]}>CEP</span>
                            <Input value={zipCode} onChange={setZipCode} icon={<Hash width={18} height={18} />} placeholder="60000-000" />
                        </div>
                    </div>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Nível de habilidade</span>
                        <div className={styles["segment"]}>
                            {SKILL_LEVELS.map((level) => (
                                <button
                                    key={level.key}
                                    type="button"
                                    onClick={() => setSkillLevel(level.key)}
                                    className={`${styles["seg-btn"]} ${skillLevel === level.key ? styles["seg-active"] : ""}`}
                                >
                                    {level.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Esportes de interesse</span>
                        <div className={styles["chips"]}>
                            {(sports ?? []).map((sport) => (
                                <button
                                    key={sport.id}
                                    type="button"
                                    onClick={() => toggleSport(sport.id)}
                                    className={`${styles["chip"]} ${sportsOfInterest.includes(sport.id) ? styles["chip-active"] : ""}`}
                                >
                                    <span className={styles["chip-icon"]}>
                                        {getSportIcon(sport.name, { width: 14, height: 14 }) ?? <Trophy width={14} height={14} />}
                                    </span>
                                    {sport.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {error && <p className={styles["error"]}>{error}</p>}
                    {saved && !error && (
                        <p className={styles["success"]}><Check width={15} height={15} /> Dados atualizados com sucesso.</p>
                    )}

                    <Button type="button" onClick={handleSave} className={styles["save-btn"]}>
                        {updateProfile.isPending ? "Salvando..." : "Salvar alterações"}
                    </Button>
                </section>
            </main>
        </div>
    );
}

export default Account;
