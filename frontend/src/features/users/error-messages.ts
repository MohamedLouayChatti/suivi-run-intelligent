import { ApiError } from "@/services/api/errors"

/**
 * French wording for the refusals the user administration endpoints can answer with.
 *
 * Unlike the Knowledge Base's errors, none of these carry a written sentence: every one is
 * translated by the generic handler, so the whole body is `{ detail: "<TypeName>" }` and there
 * is nothing to show the operator unless it is written here. Keyed on `ApiError.code` rather
 * than on the message, the code being the stable half.
 *
 * Each entry says what was refused *and* what to do about it, because every one of these is
 * correctable from the sheet the message is shown in — which is the whole reason the sheet
 * stays open on failure.
 */
const messagesByCode: Record<string, string> = {
  PermissionPrerequisiteNotSatisfied:
    "Une permission dépend d'une autre qui n'est pas accordée. Cochez d'abord les permissions requises, puis réessayez.",
  FunctionalTeamNotAllowedForApplication:
    "AERO et VIO sont assurées par l'équipe SN3 uniquement : l'équipe fonctionnelle choisie est incompatible avec l'application affectée.",
  PrimaryApplicationRequiredForRole:
    "Ce rôle nécessite une application principale. Renseignez-la avant de l'attribuer.",
  BackupWithoutPrimaryApplication:
    "Une application de secours nécessite d'abord une application principale.",
  MultiplePrimaryApplications: "Un utilisateur ne peut avoir qu'une seule application principale.",
  MultipleBackupApplications: "Un utilisateur ne peut avoir qu'une seule application de secours.",
  DuplicateApplicationAssignment:
    "La même application ne peut pas être affectée deux fois au même utilisateur.",
  // Both mean the sheet was working from a stale view of the user: it only ever sends the
  // difference between what is checked and what the user effectively holds, so either one
  // says somebody else changed the same account in the meantime.
  PermissionAlreadyGranted:
    "Cette permission a déjà été accordée entre-temps. Rouvrez la fiche pour repartir de l'état actuel.",
  PermissionNotGranted:
    "Cette permission a déjà été retirée entre-temps. Rouvrez la fiche pour repartir de l'état actuel.",
  InvalidAssignedRole: "Le rôle sélectionné est invalide.",
  RoleNotFound: "Le rôle sélectionné n'existe plus. Rouvrez la fiche pour recharger la liste.",
  UserNotFound: "Cet utilisateur n'existe plus.",
}

/** The sentence to show for a failed user administration request. */
function describeUserAdminError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "Une erreur inattendue est survenue. Réessayez."
  }
  if (error.code && messagesByCode[error.code]) {
    return messagesByCode[error.code]
  }
  // The self-targeting refusals `UserAccessPolicy` applies. The sheet already hides these
  // controls on the actor's own record, so reaching one means the interface and the backend
  // disagree — worth saying plainly rather than showing a bare type name.
  if (error.status === 403) {
    return "Vous n'avez pas les permissions nécessaires pour cette action, ou elle ne peut pas être effectuée sur votre propre compte."
  }
  // Either the backend's own sentence, or its exception name when it wrote none — the second
  // reads as a defect, which is exactly what an unmapped code without a message is.
  return error.message
}

export { describeUserAdminError }
