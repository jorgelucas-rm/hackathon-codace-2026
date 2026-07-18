import { useMutation } from "@tanstack/react-query";
import { login, loginCompany } from "../../../services/auth.service";


export function useLogin() {
    return useMutation({
        mutationFn: login
    })
}

export function useLoginCompany() {
    return useMutation({
        mutationFn: loginCompany
    })
}
