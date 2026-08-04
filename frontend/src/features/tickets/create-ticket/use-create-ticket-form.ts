"use client"

import { useState } from "react"

import type { components } from "@/types/api"

type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]

interface CreateTicketFormState {
  title: string
  description: string
  priority: TicketCreateRequest["priority"]
  category: TicketCreateRequest["category"]
  application: TicketCreateRequest["application"]
  offer: TicketCreateRequest["offer"] | ""
  version: TicketCreateRequest["version"] | ""
  element: TicketCreateRequest["element"] | ""
  operationalHighlight: boolean
  oceaneId: string
  genergyId: string
  jiraId: string
  requiresJira: boolean
  jiraDeliveryDate: string
  vioApp: TicketCreateRequest["vio_app"] | ""
}

function buildInitialState(defaultApplication: CreateTicketFormState["application"]): CreateTicketFormState {
  return {
    title: "",
    description: "",
    priority: "P3",
    category: "Bug",
    application: defaultApplication,
    offer: "",
    version: "",
    element: "",
    operationalHighlight: false,
    oceaneId: "",
    genergyId: "",
    jiraId: "",
    requiresJira: false,
    jiraDeliveryDate: "",
    vioApp: "",
  }
}

/**
 * `defaultApplication` seeds the Application field — it should be the creating user's primary
 * application (the only field they may still have a second option for: their backup app).
 */
function useCreateTicketForm(defaultApplication: CreateTicketFormState["application"]) {
  const [values, setValues] = useState<CreateTicketFormState>(() => buildInitialState(defaultApplication))

  function setField<K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  // Which Métier fields apply (offer/version, element, or vio_app) depends on the application
  // (see Ticket._validate_conditional_fields in the backend) — clear the ones that no longer
  // apply so a stale value from a previous selection can't violate that on submit.
  function setApplication(application: CreateTicketFormState["application"]) {
    setValues((prev) => ({ ...prev, application, offer: "", version: "", element: "", vioApp: "" }))
  }

  function reset() {
    setValues(buildInitialState(defaultApplication))
  }

  const isValid =
    values.title.trim().length > 0 &&
    values.description.trim().length > 0 &&
    (!values.requiresJira || values.jiraId.trim().length > 0) &&
    (values.application !== "COLORIS" || (values.offer !== "" && values.version !== "")) &&
    (values.application !== "AERO" || values.element !== "") &&
    (values.application !== "VIO" || values.vioApp !== "")

  return { values, setField, setApplication, reset, isValid }
}

export { useCreateTicketForm }
export type { CreateTicketFormState }
