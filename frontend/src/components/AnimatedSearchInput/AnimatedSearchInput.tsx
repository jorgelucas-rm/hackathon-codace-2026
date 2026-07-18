import { InputHTMLAttributes } from "react";
import { useTypewriter } from "../../hooks/useTypewriter";

export const SEARCH_PLACEHOLDERS = [
    "Buscar quadras, esportes ou locais...",
    "arena de vôlei",
    "beach tênis",
    "quadra de futebol society",
    "padel perto de você",
];

interface AnimatedSearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "placeholder"> {
    placeholders?: string[];
}

/** `<input>` com placeholder animado (digita/apaga em loop) — usado nas
 * barras de busca da Home e de Quadras para manter o mesmo efeito. */
export function AnimatedSearchInput({ placeholders = SEARCH_PLACEHOLDERS, ...rest }: AnimatedSearchInputProps) {
    const placeholder = useTypewriter(placeholders);
    return <input placeholder={placeholder} {...rest} />;
}

export default AnimatedSearchInput;
