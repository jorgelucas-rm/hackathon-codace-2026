import { useEffect, useState } from "react";

interface TypewriterOptions {
    typingSpeed?: number;
    deletingSpeed?: number;
    pauseAfterTyping?: number;
    pauseAfterDeleting?: number;
}

type Phase = "typing" | "deleting";

/** Cicla pelas `phrases`, digitando e apagando uma por vez — usado no
 * placeholder animado da busca da Home. */
export function useTypewriter(phrases: string[], options: TypewriterOptions = {}): string {
    const {
        typingSpeed = 55,
        deletingSpeed = 28,
        pauseAfterTyping = 1800,
        pauseAfterDeleting = 300,
    } = options;

    const [phraseIndex, setPhraseIndex] = useState(0);
    const [text, setText] = useState("");
    const [phase, setPhase] = useState<Phase>("typing");

    useEffect(() => {
        if (phrases.length === 0) return;

        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            setText(phrases[0]);
            return;
        }

        const current = phrases[phraseIndex % phrases.length];

        if (phase === "typing") {
            if (text.length < current.length) {
                const timer = setTimeout(() => setText(current.slice(0, text.length + 1)), typingSpeed);
                return () => clearTimeout(timer);
            }
            const timer = setTimeout(() => setPhase("deleting"), pauseAfterTyping);
            return () => clearTimeout(timer);
        }

        if (text.length > 0) {
            const timer = setTimeout(() => setText(current.slice(0, text.length - 1)), deletingSpeed);
            return () => clearTimeout(timer);
        }
        const timer = setTimeout(() => {
            setPhraseIndex((i) => (i + 1) % phrases.length);
            setPhase("typing");
        }, pauseAfterDeleting);
        return () => clearTimeout(timer);
    }, [text, phase, phraseIndex, phrases, typingSpeed, deletingSpeed, pauseAfterTyping, pauseAfterDeleting]);

    return text;
}
