export interface PatientBiometrics {
	age: string;
	gender: string;
	height: string;
	weight: string;
	notes: string;
}

const STORAGE_KEY = 'patientBiometrics';

function isBrowser() {
	return typeof window !== 'undefined';
}

function readStore(): Record<string, PatientBiometrics> {
	if (!isBrowser()) return {};

	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (!raw) return {};

		const parsed = JSON.parse(raw);
		return parsed && typeof parsed === 'object' ? parsed : {};
	} catch {
		return {};
	}
}

function writeStore(store: Record<string, PatientBiometrics>) {
	if (!isBrowser()) return;
	window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

export function savePatientBiometrics(patientId: number, biometrics: PatientBiometrics) {
	const store = readStore();
	store[String(patientId)] = biometrics;
	writeStore(store);
}

export function getPatientBiometrics(patientId: number | null | undefined): PatientBiometrics | null {
	if (!patientId) return null;
	const store = readStore();
	return store[String(patientId)] || null;
}

export function coerceBiometrics(source?: Partial<PatientBiometrics> | null): PatientBiometrics {
	return {
		age: source?.age ? String(source.age) : '',
		gender: source?.gender ? String(source.gender) : '',
		height: source?.height ? String(source.height) : '',
		weight: source?.weight ? String(source.weight) : '',
		notes: source?.notes ? String(source.notes) : ''
	};
}

export function getLatestSubmissionBiometrics(videos: Array<any> | null | undefined): PatientBiometrics | null {
	if (!videos?.length) return null;

	for (const video of videos) {
		const biometrics = video?.biometrics;
		if (!biometrics) continue;

		if (biometrics.age || biometrics.gender || biometrics.height || biometrics.weight || biometrics.notes) {
			return coerceBiometrics(biometrics);
		}
	}

	return null;
}
