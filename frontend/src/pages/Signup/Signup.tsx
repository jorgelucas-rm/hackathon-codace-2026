import { useState } from "react";
import { User, Mail, Lock, Eye, EyeOff, Building2, MapPin, Hash } from "lucide-react";
import { UserType } from "../../services/auth.service";
import { useSignup, useSignupCompany } from "./hooks/useSignup";
import { Logo } from "../../components/Logo/Logo";
import { Input } from "../../components/inputs/Input";
import { Button } from "../../components/button/Button";
import styles from "./Signup.module.scss";

interface SignupProps {
    onSignup: () => void;
    onBack: () => void;
}

const STRENGTH_LABELS = ["Muito fraca", "Fraca", "Boa", "Excelente!"];
const STRENGTH_COLORS = ["#E8D7BD", "#F27A3F", "#AD9900", "#2FAFA0"];

const ACCOUNT_TYPES = [
    { key: "user" as UserType, Icon: User, label: "Jogador" },
    { key: "company" as UserType, Icon: Building2, label: "Empresa" },
];

export function Signup({ onSignup, onBack }: SignupProps) {
    const signupUser = useSignup();
    const signupCompany = useSignupCompany();
    const [userType, setUserType] = useState<UserType>("user");
    const [showPass, setShowPass] = useState(false);

    // Campos comuns
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // Campos de empresa
    const [cnpj, setCnpj] = useState("");
    const [street, setStreet] = useState("");
    const [number, setNumber] = useState("");
    const [neighborhood, setNeighborhood] = useState("");
    const [city, setCity] = useState("");
    const [state, setState] = useState("");
    const [zipCode, setZipCode] = useState("");

    const isCompany = userType === "company";
    const isPending = signupUser.isPending || signupCompany.isPending;

    const strength = password.length >= 12 ? 3 : password.length >= 8 ? 2 : password.length >= 4 ? 1 : 0;
    const strengthColor = STRENGTH_COLORS[strength];

    const userValid = !!name && !!email && !!password;
    const companyValid = !!cnpj && !!name && !!email && !!password
        && !!street && !!number && !!neighborhood && !!city && !!state && !!zipCode;

    const handleCreate = () => {
        if (isCompany) {
            if (!companyValid) return;
            signupCompany.mutate(
                { cnpj, name, email, password, street, number, neighborhood, city, state, zip_code: zipCode },
                { onSuccess: onSignup }
            );
        } else {
            if (!userValid) return;
            signupUser.mutate({ name, email, password }, { onSuccess: onSignup });
        }
    };

    const passwordField = (
        <Input
            type={showPass ? "text" : "password"}
            placeholder="Crie uma senha"
            value={password}
            onChange={setPassword}
            icon={<Lock width={18} height={18} />}
            rightEl={
                <button type="button" onClick={() => setShowPass(!showPass)} className={styles["eye"]}>
                    {showPass ? <EyeOff width={18} height={18} /> : <Eye width={18} height={18} />}
                </button>
            }
        />
    );

    const strengthMeter = password.length > 0 && (
        <div className={styles["strength"]}>
            <div className={styles["strength-bars"]}>
                {[1, 2, 3].map((i) => (
                    <span key={i} style={{ background: i <= strength ? strengthColor : "var(--bg-secondary)" }} />
                ))}
            </div>
            <p style={{ color: strengthColor }}>{STRENGTH_LABELS[strength]}</p>
        </div>
    );

    return (
        <div className={styles["container"]}>
            <div className={styles["auth-shell"]}>
                <div className={styles["brand"]}>
                    <Logo size="lg" />
                    <p className={styles["subtitle"]}>Crie sua conta e comece a reservar hoje.</p>
                </div>

                <div className={styles["card"]}>
                    {/* Ação: Entrar / Criar conta */}
                    <div className={styles["segment"]}>
                        <button type="button" onClick={onBack} className={styles["seg-btn"]}>Entrar</button>
                        <button type="button" className={`${styles["seg-btn"]} ${styles["seg-active"]}`}>Criar conta</button>
                    </div>

                    {/* Tipo de conta: Jogador / Empresa */}
                    <div className={styles["field-group"]}>
                        <span className={styles["field-label"]}>Tipo de conta</span>
                        <div className={styles["segment"]}>
                            {ACCOUNT_TYPES.map((tab) => (
                                <button
                                    key={tab.key}
                                    type="button"
                                    onClick={() => setUserType(tab.key)}
                                    className={`${styles["seg-btn"]} ${userType === tab.key ? styles["seg-active"] : ""}`}
                                >
                                    <tab.Icon width={16} height={16} /> {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {!isCompany ? (
                        <div className={styles["fields"]}>
                            <Input type="text" placeholder="Seu nome completo" value={name} onChange={setName} icon={<User width={18} height={18} />} />
                            <Input type="email" placeholder="Seu e-mail" value={email} onChange={setEmail} icon={<Mail width={18} height={18} />} />
                            {passwordField}
                            {strengthMeter}
                        </div>
                    ) : (
                        <>
                            <div className={styles["fields"]}>
                                <span className={styles["section-label"]}>Dados da empresa</span>
                                <Input type="text" placeholder="CNPJ" value={cnpj} onChange={setCnpj} icon={<Hash width={18} height={18} />} />
                                <Input type="text" placeholder="Nome da empresa" value={name} onChange={setName} icon={<Building2 width={18} height={18} />} />
                                <Input type="email" placeholder="E-mail da empresa" value={email} onChange={setEmail} icon={<Mail width={18} height={18} />} />
                                {passwordField}
                                {strengthMeter}
                            </div>

                            <div className={styles["fields"]}>
                                <span className={styles["section-label"]}>Endereço</span>
                                <Input type="text" placeholder="Rua" value={street} onChange={setStreet} icon={<MapPin width={18} height={18} />} />
                                <div className={styles["field-row"]}>
                                    <Input type="text" placeholder="Número" value={number} onChange={setNumber} />
                                    <Input type="text" placeholder="CEP" value={zipCode} onChange={setZipCode} />
                                </div>
                                <Input type="text" placeholder="Bairro" value={neighborhood} onChange={setNeighborhood} />
                                <div className={styles["field-row-city"]}>
                                    <Input type="text" placeholder="Cidade" value={city} onChange={setCity} />
                                    <Input type="text" placeholder="UF" value={state} onChange={(v) => setState(v.toUpperCase().slice(0, 2))} />
                                </div>
                            </div>
                        </>
                    )}

                    <p className={styles["terms"]}>
                        Ao criar conta, você concorda com nossos <strong>Termos de Uso</strong> e <strong>Política de Privacidade</strong>.
                    </p>
                    <Button
                        type="button"
                        onClick={handleCreate}
                        {...{ disabled: isPending || (isCompany ? !companyValid : !userValid) }}
                    >
                        {isPending ? "Criando conta..." : isCompany ? "Criar conta da empresa" : "Criar minha conta"}
                    </Button>
                </div>
            </div>
        </div>
    );
}

export default Signup;
