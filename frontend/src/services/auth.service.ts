// Service de autenticação.
// Integração real com o backend (FastAPI, prefixo /api). Envelope de resposta:
// { code, message, error_code, data, status }. O token vem em `data` no login.
// Deixe MOCK_AUTH = true para voltar aos dados mockados.

const MOCK_AUTH = false;

export type UserType = "user" | "company";

export interface LoginData {
    email: string;
    password: string;
}

// Empresa entra com CNPJ + senha (não usa e-mail)
export interface CompanyLoginData {
    cnpj: string;
    password: string;
}

export interface SignupData {
    name: string;
    email: string;
    password: string;
}

export interface CompanySignupData {
    cnpj: string;
    name: string;
    email: string;
    password: string;
    street: string;
    number: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
}

export interface UserRead {
    id: number;
    name: string;
    email: string;
    role: string;
    situation: boolean;
    avatar?: string | null;
    phone?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    sports_of_interest: number[];
    favorite_courts: number[];
    skill_level?: string | null;
}

export interface MeUserRead {
    auth_type: string;
    entity: UserRead | null;
}

const TOKEN_KEY = "reservae_token";

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

interface Envelope<T> {
    code: number;
    message: string;
    error_code?: string | null;
    data: T;
}

async function postJson<T>(url: string, body: unknown, fallbackError: string): Promise<Envelope<T>> {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    const json = await res.json().catch(() => null);
    if (!res.ok) {
        throw new Error(json?.message || fallbackError);
    }
    return json as Envelope<T>;
}

async function getJsonAuth<T>(url: string, fallbackError: string): Promise<Envelope<T>> {
    const token = getToken();
    const res = await fetch(url, {
        method: "GET",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    const json = await res.json().catch(() => null);
    if (!res.ok) {
        throw new Error(json?.message || fallbackError);
    }
    return json as Envelope<T>;
}

export async function login(data: LoginData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        return { token: "mock-token", user: { name: "João Silva", email: data.email } };
    }

    const json = await postJson<string>("/api/auth/user-login", data, "Erro ao fazer o login");
    if (json.data) localStorage.setItem(TOKEN_KEY, json.data);
    return json;
}

export async function loginCompany(data: CompanyLoginData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        return { token: "mock-token", company: { name: "Arena Beira-Mar", cnpj: data.cnpj } };
    }

    const json = await postJson<string>("/api/auth/company-login", data, "Erro ao fazer o login");
    if (json.data) localStorage.setItem(TOKEN_KEY, json.data);
    return json;
}

export async function signup(data: SignupData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1400));
        return { token: "mock-token", user: { name: data.name, email: data.email } };
    }

    // Cadastro de jogador → POST /api/users (UserCreateDTO). A rota não
    // retorna token, então logamos em seguida com as mesmas credenciais
    // para já deixar o usuário autenticado.
    const created = await postJson<unknown>("/api/users", data, "Erro ao criar a conta");
    await login({ email: data.email, password: data.password });
    return created;
}

export async function signupCompany(data: CompanySignupData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1400));
        return { token: "mock-token", company: { name: data.name, email: data.email } };
    }

    // Cadastro de empresa → POST /api/companies (CompanyCreateDTO). Mesma
    // situação do signup de jogador: sem token na resposta, então logamos
    // em seguida com as mesmas credenciais.
    const created = await postJson<unknown>("/api/companies", data, "Erro ao criar a conta");
    await loginCompany({ cnpj: data.cnpj, password: data.password });
    return created;
}

export async function getMe() {
    const json = await getJsonAuth<MeUserRead>("/api/auth/me", "Erro ao buscar o usuário atual");
    return json.data;
}
