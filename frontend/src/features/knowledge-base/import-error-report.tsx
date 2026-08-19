"use client"

import { useMemo, useState } from "react"
import { AlertTriangle, Download, Search } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Pagination } from "@/components/app/pagination"
import type { BatchImportRejection, TicketImportError } from "@/services/api/knowledge-base"

const PAGE_SIZE = 15

/** The header row is line 1, so a problem reported against it belongs to the columns, not a ticket. */
const HEADER_LINE = 1

interface ImportErrorReportProps {
  rejection: BatchImportRejection
  fileName: string
}

/**
 * Every problem the backend found in one file, and nothing else on screen while it is shown.
 *
 * Three things make this report actionable rather than merely accurate. The line number is the
 * uploaded file's own — the row heading Excel shows in the margin, the editor line for a CSV —
 * so an operator can go straight there. Header problems are separated from row problems, because
 * a wrong column name is one fix that would otherwise look like hundreds of broken rows. And the
 * whole list is downloadable, since fixing forty rows from a scrolling table means losing your
 * place forty times.
 */
function ImportErrorReport({ rejection, fileName }: ImportErrorReportProps) {
  const [query, setQuery] = useState("")
  const [columnFilter, setColumnFilter] = useState<"all" | string>("all")
  const [rawPage, setRawPage] = useState(1)

  const headerErrors = rejection.errors.filter((error) => error.line === HEADER_LINE)
  const rowErrors = rejection.errors.filter((error) => error.line !== HEADER_LINE)
  const isTruncated = rejection.total_error_count > rejection.errors.length

  const columns = useMemo(
    () => [...new Set(rowErrors.map((error) => error.column).filter((c): c is string => c !== null))].sort(),
    [rowErrors],
  )

  const filtered = useMemo(
    () =>
      rowErrors.filter(
        (error) =>
          (columnFilter === "all" || error.column === columnFilter) &&
          (query === "" ||
            `${error.line} ${error.column ?? ""} ${error.value ?? ""} ${error.message}`
              .toLowerCase()
              .includes(query.toLowerCase())),
      ),
    [rowErrors, query, columnFilter],
  )

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(rawPage, pageCount)
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const affectedLines = new Set(rowErrors.map((error) => error.line)).size

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-destructive/40 bg-destructive/5 p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" strokeWidth={2} />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground">
              Fichier refusé — aucun ticket n&apos;a été importé
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {rejection.total_error_count.toLocaleString("fr-FR")}{" "}
              {rejection.total_error_count > 1 ? "problèmes détectés" : "problème détecté"} dans{" "}
              <span className="font-medium text-foreground">{fileName}</span>
              {affectedLines > 0 && (
                <>
                  , sur {affectedLines.toLocaleString("fr-FR")}{" "}
                  {affectedLines > 1 ? "lignes" : "ligne"}
                </>
              )}
              . Corrigez-les puis déposez le fichier à nouveau&nbsp;: l&apos;import est tout ou rien,
              rien n&apos;a été écrit en base.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="shrink-0"
            onClick={() => downloadErrorReport(rejection, fileName)}
          >
            <Download className="size-4" /> Exporter la liste
          </Button>
        </div>
      </div>

      {isTruncated && (
        <p className="rounded-md border border-border bg-surface px-4 py-3 text-sm text-muted-foreground">
          Seules les {rejection.errors.length.toLocaleString("fr-FR")} premières erreurs sont
          détaillées ci-dessous, sur {rejection.total_error_count.toLocaleString("fr-FR")} au total.
          Un fichier qui échoue sur autant de lignes a le plus souvent une seule cause commune —
          traitez-la d&apos;abord, puis redéposez le fichier pour voir ce qu&apos;il reste.
        </p>
      )}

      {headerErrors.length > 0 && (
        <div className="rounded-md border border-border bg-surface">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-medium">Ligne d&apos;en-tête</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Les colonnes du fichier n&apos;ont pas pu être reconnues, donc aucune ligne n&apos;a été
              lue. Corrigez l&apos;en-tête en premier.
            </p>
          </div>
          <ul className="divide-y divide-border">
            {headerErrors.map((error, index) => (
              <li key={index} className="px-4 py-3 text-sm">
                {error.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {rowErrors.length > 0 && (
        <div className="rounded-md border border-border">
          <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
            <div className="relative min-w-0 flex-1 basis-64">
              <Search
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
                strokeWidth={1.75}
              />
              <Input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value)
                  setRawPage(1)
                }}
                placeholder="Rechercher une ligne, une colonne ou un message…"
                className="pl-9"
              />
            </div>
            <Select
              value={columnFilter}
              onValueChange={(value) => {
                setColumnFilter(value)
                setRawPage(1)
              }}
            >
              <SelectTrigger className="w-[14rem]">
                <SelectValue placeholder="Colonne" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Toutes les colonnes</SelectItem>
                {columns.map((column) => (
                  <SelectItem key={column} value={column}>
                    {column}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-20">Ligne</TableHead>
                <TableHead className="w-48">Colonne</TableHead>
                <TableHead className="w-48">Valeur lue</TableHead>
                <TableHead>Problème</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell
                    colSpan={4}
                    className="py-8 text-center text-sm whitespace-normal text-muted-foreground"
                  >
                    Aucune erreur ne correspond à ces critères.
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((error, index) => (
                  <TableRow key={`${error.line}-${error.column}-${index}`} className="hover:bg-transparent">
                    <TableCell className="font-mono text-xs tabular text-muted-foreground">
                      {error.line}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {error.column ?? (
                        <Badge variant="secondary" className="bg-foreground/10 text-foreground/70">
                          ligne entière
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs break-all text-muted-foreground">
                      {error.value ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm whitespace-normal">{error.message}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          <Pagination
            page={page}
            pageCount={pageCount}
            onPageChange={setRawPage}
            className="border-t border-border"
          />
        </div>
      )}
    </div>
  )
}

function escapeCsvCell(value: string): string {
  return /[",\r\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value
}

function errorReportCsv(errors: TicketImportError[]): string {
  const header = ["Ligne", "Colonne", "Valeur lue", "Problème"].map(escapeCsvCell).join(",")
  const rows = errors.map((error) =>
    [String(error.line), error.column ?? "", error.value ?? "", error.message]
      .map(escapeCsvCell)
      .join(","),
  )
  return `﻿${[header, ...rows].join("\r\n")}\r\n`
}

function downloadErrorReport(rejection: BatchImportRejection, fileName: string) {
  const blob = new Blob([errorReportCsv(rejection.errors)], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `erreurs_${fileName.replace(/\.[^.]+$/, "")}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

export { ImportErrorReport }
