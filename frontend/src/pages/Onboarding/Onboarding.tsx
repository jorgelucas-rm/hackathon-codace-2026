import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "../../components/button/Button";
import { Logo } from "../../components/Logo/Logo";
import sportsBall from "../../assets/logo.png";
import styles from "./Onboarding.module.scss";

interface OnboardingProps {
    onDone: () => void;
}

const SLIDES = [
    {
        title: "Sua próxima partida\ncomeça aqui.",
        desc: "Encontre quadras, escolha um horário e reserve em poucos segundos.",
        cta: "Próximo",
    },
    {
        title: "Jogue do\nseu jeito.",
        desc: "Crie grupos, convide amigos ou entre em partidas abertas perto de você.",
        cta: "Começar",
    },
];

export function Onboarding({ onDone }: OnboardingProps) {
    const [step, setStep] = useState(0);
    const slide = SLIDES[step];
    const isLast = step === SLIDES.length - 1;

    return (
        <div className={styles["container"]}>
            <div className={styles["bg-glow"]} aria-hidden />

            <header className={styles["top-bar"]}>
                <Logo size="md" />
            </header>
            <button onClick={onDone} className={styles["skip"]}>Pular</button>

            <main className={styles["stage"]}>
                <div className={styles["ball-area"]}>
                    <div className={styles["glow"]} />
                    <img src={sportsBall} alt="Esfera multiesporte" className={styles["ball"]} />
                </div>

                <div key={step} className={styles["text-block"]}>
                    <h1 className={styles["title"]}>{slide.title}</h1>
                    <p className={styles["desc"]}>{slide.desc}</p>
                </div>

                <div className={styles["dots"]}>
                    {SLIDES.map((_, i) => (
                        <span key={i} className={`${styles["dot"]} ${i === step ? styles["dot-active"] : ""}`} />
                    ))}
                </div>

                <div className={styles["cta-wrap"]}>
                    <Button
                        type="button"
                        className={styles["next-button"]}
                        onClick={() => (isLast ? onDone() : setStep(step + 1))}
                    >
                        {slide.cta} <ArrowRight width={18} height={18} />
                    </Button>
                </div>
            </main>
        </div>
    );
}

export default Onboarding;
