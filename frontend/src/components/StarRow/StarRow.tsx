import { Star } from "lucide-react";
import styles from "./StarRow.module.scss";

interface StarRowProps {
    rating: number;
    size?: "sm" | "md";
}

export function StarRow({ rating, size = "sm" }: StarRowProps) {
    const px = size === "md" ? 16 : 12;
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
