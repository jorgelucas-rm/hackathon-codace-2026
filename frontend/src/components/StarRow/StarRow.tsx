import { Star } from "lucide-react";
import styles from "./StarRow.module.scss";

interface StarRowProps {
    rating: number;
    size?: "sm" | "md";
    onRate?: (rating: number) => void;
}

export function StarRow({ rating, size = "sm", onRate }: StarRowProps) {
    const px = size === "md" ? 16 : 12;

    if (onRate) {
        return (
            <div className={styles["row"]} role="radiogroup" aria-label="Nota de 1 a 5 estrelas">
                {[1, 2, 3, 4, 5].map((i) => (
                    <button
                        key={i}
                        type="button"
                        role="radio"
                        aria-checked={i === rating}
                        aria-label={`${i} estrela${i > 1 ? "s" : ""}`}
                        className={styles["star-btn"]}
                        onClick={() => onRate(i)}
                    >
                        <Star width={px} height={px} className={i <= rating ? styles["filled"] : styles["empty"]} />
                    </button>
                ))}
            </div>
        );
    }

    return (
        <div className={styles["row"]}>
            {[1, 2, 3, 4, 5].map((i) => (
                <Star
                    key={i}
                    width={px}
                    height={px}
                    className={i <= rating ? styles["filled"] : styles["empty"]}
                />
            ))}
        </div>
    );
}

export default StarRow;
