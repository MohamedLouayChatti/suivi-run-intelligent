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
  assigneeId: string
  functionalTeam: TicketCreateRequest["functional_team"]
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

const initialCreateTicketForm: CreateTicketFormState = {
  title: "",
  description: "",
  priority: "P3",
  category: "Bug",
  application: "FCI",
  assigneeId: "",
  functionalTeam: "SUPPORT",
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

function useCreateTicketForm() {
  const [values, setValues] = useState<CreateTicketFormState>(initialCreateTicketForm)

  function setField<K extends keyof CreateTicketFormState>(key: K, value: CreateTicketFormState[K]) {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  function reset() {
    setValues(initialCreateTicketForm)
  }

  const isValid =
    values.title.trim().length > 0 &&
    values.description.trim().length > 0 &&
    (!values.requiresJira || values.jiraId.trim().length > 0) &&
    (values.application !== "VIO" || values.vioApp !== "")

  return { values, setField, reset, isValid }
}

export { useCreateTicketForm }
export type { CreateTicketFormState }
