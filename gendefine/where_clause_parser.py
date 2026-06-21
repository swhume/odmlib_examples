"""Parses inline where clause expressions from text values.

Used when the spreadsheet format embeds where clauses as text expressions
(e.g., "TESTCD EQ SYSBP") rather than in a dedicated worksheet.
"""

import logging
import re

logger = logging.getLogger(__name__)


class WhereClauseParser:
    """Parses where clause expressions from inline text values."""

    _COMPARATORS = {"EQ", "NE", "LT", "LE", "GT", "GE", "IN", "NOTIN"}

    def parse(self, expression: str, dataset: str) -> list[dict]:
        """Parse a where clause expression into structured components.

        Handles:
        - Simple: "TESTCD EQ SYSBP"
        - Compound (AND): "TESTCD EQ SYSBP AND POSITION EQ STANDING"
        - IN operator: "TESTCD IN (SYSBP, DIABP)"
        - NOTIN operator: "TESTCD NOTIN (A, B)"

        :param expression: the where clause expression string
        :param dataset: the dataset name for context
        :returns: list of dicts with variable, comparator, value, dataset
        """
        if not expression or not expression.strip():
            return []

        conditions = []
        # Split on " AND " (case-sensitive, surrounded by spaces)
        parts = re.split(r'\s+AND\s+', expression.strip())

        for part in parts:
            part = part.strip()
            if not part:
                continue
            parsed = self._parse_condition(part, dataset)
            if parsed:
                conditions.append(parsed)
            else:
                logger.warning("Could not parse where clause condition: '%s'", part)

        return conditions

    def _parse_condition(self, condition: str, dataset: str) -> dict | None:
        """Parse a single condition like 'TESTCD EQ SYSBP' or 'TESTCD IN (A, B)'.

        :returns: dict with variable, comparator, value, dataset or None on failure
        """
        # Try IN/NOTIN with parenthesized list first
        match = re.match(
            r'^(\w+)\s+(IN|NOTIN)\s+\(([^)]+)\)$',
            condition.strip()
        )
        if match:
            variable = match.group(1)
            comparator = match.group(2)
            values = [v.strip() for v in match.group(3).split(",")]
            return {
                "variable": variable,
                "comparator": comparator,
                "value": values,
                "dataset": dataset,
            }

        # Try simple comparator: VARIABLE COMP VALUE
        match = re.match(
            r'^(\w+)\s+(EQ|NE|LT|LE|GT|GE|IN|NOTIN)\s+(\S+)$',
            condition.strip()
        )
        if match:
            return {
                "variable": match.group(1),
                "comparator": match.group(2),
                "value": match.group(3),
                "dataset": dataset,
            }

        return None

    def build_where_clause_defs(self, value_level_rows: list[dict],
                                 oid_pattern: str) -> list[dict]:
        """Extract unique where clauses from value-level rows and build WhereClauseDef structures.

        Groups duplicate where clause expressions to avoid redundant definitions.
        Generates OIDs using the pattern.

        :param value_level_rows: list of value-level row dicts with 'where_clause_expr' and 'dataset'
        :param oid_pattern: OID pattern for where clauses (e.g., "WC.{Dataset}.{Variable}.{Value}")
        :returns: list of WhereClauseDef intermediate dicts
        """
        where_clauses = []
        seen_expressions = {}  # expression -> OID
        wc_counter = 0

        for row in value_level_rows:
            expr = row.get("where_clause_expr", "")
            dataset = row.get("dataset", "")
            if not expr:
                continue

            if expr in seen_expressions:
                continue

            wc_counter += 1
            conditions = self.parse(expr, dataset)
            if not conditions:
                continue

            # Generate OID from pattern or use counter-based
            oid = self._generate_wc_oid(oid_pattern, dataset, conditions, wc_counter)

            range_checks = []
            for cond in conditions:
                item_oid = f"IT.{cond['dataset']}.{cond['variable']}".upper()
                check_values = cond["value"] if isinstance(cond["value"], list) else [cond["value"]]
                range_checks.append({
                    "item_oid": item_oid,
                    "comparator": cond["comparator"],
                    "check_values": check_values,
                })

            wc = {
                "oid": oid,
                "range_checks": range_checks,
            }
            where_clauses.append(wc)
            seen_expressions[expr] = oid

        return where_clauses, seen_expressions

    def _generate_wc_oid(self, pattern: str, dataset: str,
                          conditions: list[dict], counter: int) -> str:
        """Generate a WhereClauseDef OID."""
        if conditions:
            first = conditions[0]
            variable = first["variable"]
            value = first["value"]
            if isinstance(value, list):
                value = value[0]
            oid = pattern.replace("{Dataset}", dataset)
            oid = oid.replace("{Variable}", variable)
            oid = oid.replace("{Value}", str(value))
            oid = oid.replace("{index}", str(counter))
        else:
            oid = f"WC.{counter}"
        return oid.upper()
