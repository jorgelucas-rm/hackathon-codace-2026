import { useState, useRef, useLayoutEffect } from "react";
import { Mail, Lock, Eye, EyeOff, User, Building2, Hash, MapPin, ArrowRight, ArrowLeft } from "lucide-react";
import { UserType } from "../../services/auth.service";
import { useLogin, useLoginCompany } from "./hooks/useLogin";
import { useSignup, useSignupCompany } from "../Signup/hooks/useSignup";
import { Input } from "../../components/inputs/Input";
import { Button } from "../../components/button/Button";
import styles from "./Login.module.scss";

interface LoginProps {
    onLogin: () => void;
}

const ACCOUNT_TYPES = [
    { key: "user" as UserType, Icon: User, label: "Jogador" },
    { key: "company" as UserType, Icon: Building2, label: "Empresa" },
];

const STRENGTH_LABELS = ["Muito fraca", "Fraca", "Boa", "Excelente!"];
const STRENGTH_COLORS = ["#E8D7BD", "#F27A3F", "#AD9900", "#2FAFA0"];

export function Login({ onLogin }: LoginProps) {
    const [mode, setMode] = useState<"login" | "signup">("login");
    const isSignup = mode === "signup";

    // ---- Login ----
    const loginUser = useLogin();
    const loginCompany = useLoginCompany();
    const [loginType, setLoginType] = useState<UserType>("user");
    const [lEmail, setLEmail] = useState("");
    const [lCnpj, setLCnpj] = useState("");
    const [lPass, setLPass] = useState("");
    const [lShow, setLShow] = useState(false);
    const [lError, setLError] = useState("");
    const lIsCompany = loginType === "company";
    const lPending = loginUser.isPending || loginCompany.isPending;

    // ---- Cadastro ----
    const signupUser = useSignup();
    const signupCompany = useSignupCompany();
    const [signupType, setSignupType] = useState<UserType>("user");
    const [sShow, setSShow] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [cnpj, setCnpj] = useState("");
    const [street, setStreet] = useState("");
    const [number, setNumber] = useState("");
    const [neighborhood, setNeighborhood] = useState("");
    const [city, setCity] = useState("");
    const [state, setState] = useState("");
    const [zipCode, setZipCode] = useState("");
    const sIsCompany = signupType === "company";
    const sPending = signupUser.isPending || signupCompany.isPending;

    const strength = password.length >= 12 ? 3 : password.length >= 8 ? 2 : password.length >= 4 ? 1 : 0;
    const strengthColor = STRENGTH_COLORS[strength];
    const userValid = !!name && !!email && !!password;
    const companyValid = !!cnpj && !!name && !!email && !!password
        && !!street && !!number && !!neighborhood && !!city && !!state && !!zipCode;

    // Altura do card acompanha o formulário visível
    const loginRef = useRef<HTMLFormElement>(null);
    const signupRef = useRef<HTMLFormElement>(null);
    const [height, setHeight] = useState<number | undefined>(undefined);
    useLayoutEffect(() => {
        const el = isSignup ? signupRef.current : loginRef.current;
        if (!el) return;
        const update = () => setHeight(el.offsetHeight);
        update();
        const ro = new ResizeObserver(update);
        ro.observe(el);
        return () => ro.disconnect();
    }, [isSignup]);

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        const identifier = lIsCompany ? lCnpj : lEmail;
        if (!identifier || !lPass) { setLError("Preencha todos os campos."); return; }
        setLError("");
        const options = { onSuccess: onLogin, onError: () => setLError("Erro ao fazer o login.") };
        if (lIsCompany) loginCompany.mutate({ cnpj: lCnpj, password: lPass }, options);
        else loginUser.mutate({ email: lEmail, password: lPass }, options);
    };

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        if (sIsCompany) {
            if (!companyValid) return;
            signupCompany.mutate(
                { cnpj, name, email, password, street, number, neighborhood, city, state, zip_code: zipCode },
                { onSuccess: onLogin }
            );
        } else {
            if (!userValid) return;
            signupUser.mutate({ name, email, password }, { onSuccess: onLogin });
        }
    };

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

    const typeSegment = (value: UserType, onChange: (t: UserType) => void) => (
        <div className={styles["segment"]}>
            {ACCOUNT_TYPES.map((tab) => (
                <button
                    key={tab.key}
                    type="button"
                    onClick={() => onChange(tab.key)}
                    className={`${styles["seg-btn"]} ${value === tab.key ? styles["seg-active"] : ""}`}
                >
                    <tab.Icon width={16} height={16} /> {tab.label}
                </button>
            ))}
        </div>
    );

    const brand = <span className={styles["overlay-brand"]}>Reserva<b>ê</b></span>;

    return (
        <div className={styles["container"]}>
            <div className={styles["auth-shell"]}>
                <div className={`${styles["split"]} ${isSignup ? styles["split-signup"] : ""}`} style={{ height }}>
                    {/* ---------- Formulário: Entrar (lado esquerdo) ---------- */}
                    <form ref={loginRef} className={`${styles["side"]} ${styles["side-login"]} ${isSignup ? styles["is-inactive"] : ""}`} onSubmit={handleLogin}>
                        <div className={styles["panel-head"]}>
                            <h2 className={styles["panel-title"]}>Entrar</h2>
                            <p className={styles["panel-sub"]}>Bem-vindo de volta — suas quadras te esperam.</p>
                        </div>

                        {typeSegment(loginType, (t) => { setLoginType(t); setLError(""); })}

                        <div className={styles["fields"]}>
                            {lIsCompany ? (
                                <Input type="text" placeholder="CNPJ da empresa" value={lCnpj} onChange={setLCnpj} icon={<Hash width={18} height={18} />} />
                            ) : (
                                <Input type="email" placeholder="Seu e-mail" value={lEmail} onChange={setLEmail} icon={<Mail width={18} height={18} />} />
                            )}
                            <Input
                                type={lShow ? "text" : "password"}
                                placeholder="Sua senha"
                                value={lPass}
                                onChange={setLPass}
                                icon={<Lock width={18} height={18} />}
                                rightEl={
                                    <button type="button" onClick={() => setLShow(!lShow)} className={styles["eye"]}>
                                        {lShow ? <EyeOff width={18} height={18} /> : <Eye width={18} height={18} />}
                                    </button>
                                }
                            />
                        </div>

                        {lError && <p className={styles["error"]}>{lError}</p>}

                        <div className={styles["forgot-row"]}>
                            <button type="button" className={styles["forgot"]}>Esqueci a senha</button>
                        </div>

                        <Button type="submit" {...{ disabled: lPending }}>
                            {lPending ? "Entrando..." : "Entrar"}
                        </Button>
                    </form>

                    {/* ---------- Formulário: Criar conta (lado direito) ---------- */}
                    <form ref={signupRef} className={`${styles["side"]} ${styles["side-signup"]} ${!isSignup ? styles["is-inactive"] : ""}`} onSubmit={handleCreate}>
                        <div className={styles["panel-head"]}>
                            <h2 className={styles["panel-title"]}>Criar conta</h2>
                            <p className={styles["panel-sub"]}>Rápido e gratuito. Comece a reservar agora.</p>
                        </div>

                        {typeSegment(signupType, setSignupType)}

                        {!sIsCompany ? (
                            <>
                                <div className={styles["grid"]}>
                                    <Input type="text" placeholder="Nome completo" value={name} onChange={setName} icon={<User width={18} height={18} />} />
                                    <Input type="email" placeholder="E-mail" value={email} onChange={setEmail} icon={<Mail width={18} height={18} />} />
                                    <div className={styles["span-2"]}>
                                        <Input
                                            type={sShow ? "text" : "password"}
                                            placeholder="Crie uma senha"
                                            value={password}
                                            onChange={setPassword}
                                            icon={<Lock width={18} height={18} />}
                                            rightEl={
                                                <button type="button" onClick={() => setSShow(!sShow)} className={styles["eye"]}>
                                                    {sShow ? <EyeOff width={18} height={18} /> : <Eye width={18} height={18} />}
                                                </button>
                                            }
                                        />
                                    </div>
                                </div>
                                {strengthMeter}
                            </>
                        ) : (
                            <>
                                <span className={styles["section-label"]}>Dados da empresa</span>
                                <div className={styles["grid"]}>
                                    <div className={styles["span-2"]}>
                                        <Input type="text" placeholder="Nome da empresa" value={name} onChange={setName} icon={<Building2 width={18} height={18} />} />
                                    </div>
                                    <Input type="text" placeholder="CNPJ" value={cnpj} onChange={setCnpj} icon={<Hash width={18} height={18} />} />
                                    <Input type="email" placeholder="E-mail" value={email} onChange={setEmail} icon={<Mail width={18} height={18} />} />
                                    <div className={styles["span-2"]}>
                                        <Input
                                            type={sShow ? "text" : "password"}
                                            placeholder="Crie uma senha"
                                            value={password}
                                            onChange={setPassword}
                                            icon={<Lock width={18} height={18} />}
                                            rightEl={
                                                <button type="button" onClick={() => setSShow(!sShow)} className={styles["eye"]}>
                                                    {sShow ? <EyeOff width={18} height={18} /> : <Eye width={18} height={18} />}
                                                </button>
                                            }
                                        />
                                    </div>
                                </div>
                                {strengthMeter}

                                <span className={styles["section-label"]}>Endereço</span>
                                <div className={styles["grid"]}>
                                    <div className={styles["span-2"]}>
                                        <Input type="text" placeholder="Rua / Endereço" value={street} onChange={setStreet} icon={<MapPin width={18} height={18} />} />
                                    </div>
                                    <Input type="text" placeholder="Número" value={number} onChange={setNumber} />
                                    <Input type="text" placeholder="CEP" value={zipCode} onChange={setZipCode} />
                                    <div className={styles["span-2"]}>
                                        <Input type="text" placeholder="Bairro" value={neighborhood} onChange={setNeighborhood} />
                                    </div>
                                    <Input type="text" placeholder="Cidade" value={city} onChange={setCity} />
                                    <Input type="text" placeholder="UF" value={state} onChange={(v) => setState(v.toUpperCase().slice(0, 2))} />
                                </div>
                            </>
                        )}

                        <p className={styles["terms"]}>
                            Ao criar conta, você concorda com nossos <strong>Termos de Uso</strong> e <strong>Política de Privacidade</strong>.
                        </p>

                        <Button type="submit" {...{ disabled: sPending || (sIsCompany ? !companyValid : !userValid) }}>
                            {sPending ? "Criando conta..." : "Criar conta"}
                        </Button>
                    </form>

                    {/* ---------- Painel escuro deslizante (indica o outro fluxo) ---------- */}
                    <div className={styles["overlay"]}>
                        <div className={styles["overlay-glow"]} />
                        <div className={`${styles["overlay-inner"]} ${!isSignup ? styles["overlay-inner-active"] : ""}`}>
                            {brand}
                            <div>
                                <p className={styles["overlay-eyebrow"]}>Novo por aqui?</p>
                                <h3 className={styles["overlay-title"]}>Crie sua conta</h3>
                                <p className={styles["overlay-text"]}>Reserve quadras em segundos e entre em partidas abertas perto de você.</p>
                            </div>
                            <button type="button" onClick={() => setMode("signup")} className={styles["overlay-btn"]}>
                                Criar conta <ArrowRight width={16} height={16} />
                            </button>
                        </div>

                        <div className={`${styles["overlay-inner"]} ${isSignup ? styles["overlay-inner-active"] : ""}`}>
                            {brand}
                            <div>
                                <p className={styles["overlay-eyebrow"]}>Já tem conta?</p>
                                <h3 className={styles["overlay-title"]}>Bom te ver de volta</h3>
                                <p className={styles["overlay-text"]}>Entre e continue de onde parou — suas reservas te esperam.</p>
                            </div>
                            <button type="button" onClick={() => setMode("login")} className={styles["overlay-btn"]}>
                                <ArrowLeft width={16} height={16} /> Entrar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Login;
