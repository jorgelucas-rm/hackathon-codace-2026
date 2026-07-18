import { ReactElement, SVGProps } from "react";
import { Volleyball } from "lucide-react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function base({ size = 20, width, height, ...props }: IconProps) {
    return { width: width ?? size, height: height ?? size, ...props };
}

/** Futebol Society */
export function SoccerBallIcon(props: IconProps) {
    const { width, height, ...rest } = base(props);
    return (
        <svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" {...rest}>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7.2 15 9.4l-1.2 3.6h-3.6L9 9.4z" />
            <path d="M12 3v4.2M4.8 8.6l4.2.8M19.2 8.6l-4.2.8M7 18l2.2-4.2M17 18l-2.2-4.2" />
        </svg>
    );
}

/** Basquete */
export function BasketballIcon(props: IconProps) {
    const { width, height, ...rest } = base(props);
    return (
        <svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" {...rest}>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 3v18M3 12h18" />
            <path d="M5.3 5.3c2.8 2.8 2.8 10.6 0 13.4M18.7 5.3c-2.8 2.8-2.8 10.6 0 13.4" />
        </svg>
    );
}

/** Padel */
export function PadelIcon(props: IconProps) {
    const { width, height, ...rest } = base(props);
    return (
        <svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" {...rest}>
            <rect x="3" y="3" width="11" height="13" rx="5.5" />
            <path d="M8.5 16.5V21" />
            <path d="M6.5 6.5h6M6.5 9.5h6M6.5 12.5h6" opacity="0.6" />
            <circle cx="18.5" cy="6.5" r="2.3" />
        </svg>
    );
}

/** Beach Tênis */
export function BeachTennisIcon(props: IconProps) {
    const { width, height, ...rest } = base(props);
    return (
        <svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" {...rest}>
            <rect x="4" y="2.5" width="10" height="12.5" rx="5" />
            <path d="M9 15v4.5" />
            <path d="M3 21c1.2 0 1.2-1.4 2.4-1.4S6.6 21 7.8 21s1.2-1.4 2.4-1.4S11.4 21 12.6 21s1.2-1.4 2.4-1.4S16.2 21 17.4 21s1.2-1.4 2.4-1.4" />
        </svg>
    );
}

/** Vôlei — reaproveita o ícone do lucide-react (mesma linguagem visual dos outros ícones da UI) */
export function VolleyballSportIcon(props: IconProps) {
    const { width, height } = base(props);
    return <Volleyball width={width} height={height} strokeWidth={1.6} />;
}

const NORMALIZED_ICONS: Record<string, (props: IconProps) => ReactElement> = {
    "futebol society": SoccerBallIcon,
    "basquete": BasketballIcon,
    "padel": PadelIcon,
    "beach tenis": BeachTennisIcon,
    "volei": VolleyballSportIcon,
};

const DIACRITICS_REGEX = new RegExp("[̀-ͯ]", "g");

function normalize(name: string): string {
    return name
        .toLowerCase()
        .normalize("NFD")
        .replace(DIACRITICS_REGEX, "")
        .trim();
}

/** Resolve o ícone SVG minimalista de um esporte pelo nome; retorna null se não houver mapeamento. */
export function getSportIcon(sportName: string, props?: IconProps): ReactElement | null {
    const Icon = NORMALIZED_ICONS[normalize(sportName)];
    return Icon ? <Icon {...props} /> : null;
}
