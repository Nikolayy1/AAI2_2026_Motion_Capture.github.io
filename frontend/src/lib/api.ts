
import { goto } from '$app/navigation';

export function getToken() {
	return (
		localStorage.getItem('access_token') ||
		sessionStorage.getItem('access_token')
	);
}

export async function apiFetch(
	url: string,
	options: RequestInit = {}
) {
	const token = getToken();

	const res = await fetch(url, {
		...options,
		headers: {
			...(options.headers || {}),
			Authorization: token ? `Bearer ${token}` : ''
		}
	});

	// Optional: auto-logout if token invalid
	if (res.status === 401) {
		localStorage.removeItem('access_token');
		sessionStorage.removeItem('access_token');
		goto('/mobile/login');
	}

	return res;
}