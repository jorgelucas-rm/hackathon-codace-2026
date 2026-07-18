// Service de partidas abertas — por enquanto retorna dados mockados.
// Quando o backend estiver pronto, basta trocar por chamadas fetch("/api/matches...").

export interface OpenMatch {
    name: string;
    location: string;
    time: string;
    players: number;
    maxPlayers: number;
    spots: number;
    level: string;
    price: string;
}

const OPEN_MATCHES: OpenMatch[] = [
    { name: "Futebol Society — Quinta", location: "Arena Prime Futebol", time: "20:00 – 21:30", players: 7, maxPlayers: 10, spots: 3, level: "Intermediário", price: "R$ 25/jogador" },
    { name: "Basquete — Sábado", location: "SportZone Fortaleza", time: "09:00 – 11:00", players: 6, maxPlayers: 12, spots: 6, level: "Iniciante", price: "R$ 20/jogador" },
    { name: "Beach Tennis Duplas", location: "Arena Beira-Mar", time: "16:00 – 18:00", players: 2, maxPlayers: 4, spots: 2, level: "Avançado", price: "R$ 35/jogador" },
];

export async function getOpenMatches(): Promise<OpenMatch[]> {
    // TODO integração: return (await fetch("/api/matches")).json();
    return OPEN_MATCHES;
}

export function getOpenMatchesSync(): OpenMatch[] {
    return OPEN_MATCHES;
}
