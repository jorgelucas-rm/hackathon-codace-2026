import { useState } from "react";
import { ChevronLeft, CheckCircle, CreditCard, CircleDot, Lock } from "lucide-react";
import { Screen } from "../../types";
import styles from "./Checkout.module.scss";

interface CheckoutProps {
    onNavigate: (screen: Screen) => void;
}

export function Checkout({ onNavigate }: CheckoutProps) {
    const [payment, setPayment] = useState<"pix" | "credit">("pix");
    const [done, setDone] = useState(false);

    if (done) {
        return (
            <div className={styles["success"]}>
                <div className={styles["success-icon"]}>
                    <CheckCircle width={48} height={48} />
                </div>
                <h1>Reserva Confirmada!</h1>
                <p>Sua reserva na Arena Beira-Mar para hoje às 19:00 foi confirmada com sucesso.</p>
                <button onClick={() => onNavigate("home")} className="button-primary">
                    Voltar para o início
                </button>
            </div>
        );
    }

    const paymentOptions = [
        { key: "pix" as const, className: styles["pay-pix"], label: "Pix", sub: "Pagamento instantâneo", node: <span>Pix</span> },
        { key: "credit" as const, className: styles["pay-credit"], label: "Cartão de Crédito", sub: "em até 12x sem juros", node: <CreditCard width={20} height={20} /> },
    ];

    return (
        <div className={styles["container"]}>
            <div className={styles["header"]}>
                <button onClick={() => onNavigate("match")} className={styles["back"]}>
                    <ChevronLeft width={20} height={20} />
                </button>
                <h1>Checkout / Pagamento</h1>
            </div>

            <div className={styles["body"]}>
                <div className={`surface-card ${styles["card"]}`}>
                    <h2>Resumo da Partida</h2>
                    <div className={styles["summary-court"]}>
                        <div className={styles["court-emoji"]}><CircleDot width={24} height={24} /></div>
                        <div>
                            <p className={styles["court-name"]}>Arena Prime Futebol · Quadra 1</p>
                            <p>Aldeota, Fortaleza — CE</p>
                            <p>Hoje · 20:00 – 21:30 · Futsal</p>
                        </div>
                    </div>
                    <div className={styles["lines"]}>
                        <div className={styles["line"]}><span>Valor de Reserva</span><strong>R$ 120,00</strong></div>
                        <div className={styles["line"]}><span>Taxa da Plataforma</span><strong>R$ 12,00</strong></div>
                        <div className={styles["total"]}>
                            <span>Total a Pagar</span>
                            <strong>R$ 132,00</strong>
                        </div>
                    </div>
                </div>

                <div className={`surface-card ${styles["card"]}`}>
                    <h2>Método de Pagamento</h2>
                    <div className={styles["payments"]}>
                        {paymentOptions.map((opt) => (
                            <button
                                key={opt.key}
                                onClick={() => setPayment(opt.key)}
                                className={`${styles["payment"]} ${payment === opt.key ? styles["payment-active"] : ""}`}
                            >
                                <div className={`${styles["pay-icon"]} ${opt.className}`}>{opt.node}</div>
                                <div className={styles["pay-info"]}>
                                    <p>{opt.label}</p>
                                    <span>{opt.sub}</span>
                                </div>
                                <div className={styles["radio"]}>
                                    {payment === opt.key && <span />}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {payment === "credit" && (
                    <div className={`surface-card ${styles["card"]}`}>
                        <h3>Dados do Cartão</h3>
                        <input className={styles["field"]} placeholder="Número do cartão" />
                        <input className={styles["field"]} placeholder="Nome no cartão" />
                        <div className={styles["field-row"]}>
                            <input className={styles["field"]} placeholder="Validade" />
                            <input className={styles["field"]} placeholder="CVV" />
                        </div>
                    </div>
                )}

                <button onClick={() => setDone(true)} className={`button-primary ${styles["confirm"]}`}>
                    Confirmar e Pagar
                </button>
                <p className={styles["secure"]}><Lock width={12} height={12} /> Pagamento 100% seguro e criptografado</p>
            </div>
        </div>
    );
}

export default Checkout;
