import re
import sqlparse
from typing import Dict, List, Set

class MinimalSQLParser:
    def __init__(self):
        # Common SQL/Spark functions
        self.sql_functions = {
            'IF', 'CASE', 'WHEN', 'THEN', 'ELSE', 'COALESCE', 'NVL',
            'TO_DATE', 'DATE_FORMAT', 'CURRENT_DATE', 'CURRENT_TIMESTAMP',
            'CAST', 'CONVERT', 'SUBSTRING', 'CONCAT', 'TRIM', 'LENGTH',
            'SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'ROW_NUMBER', 'RANK',
            'DECODE', 'UPPER', 'LOWER', 'ROUND', 'FLOOR', 'CEIL'
        }
    
    def parse_query(self, sql: str) -> Dict:
        """Extract key components from SQL query"""
        
        # Clean the query
        sql_clean = self._clean_sql(sql)
        
        result = {
            "tables": self._extract_tables(sql_clean),
            "columns": self._extract_columns(sql_clean),
            "functions": self._extract_functions(sql_clean),
            "description": self._generate_description(sql_clean)
        }
        
        return result
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL string - remove extra quotes, normalize whitespace"""
        # Remove triple quotes if present
        sql = re.sub(r'["\'"]{3}', '', sql)
        # Normalize whitespace
        sql = ' '.join(sql.split())
        return sql
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from FROM and JOIN clauses"""
        tables = set()
        
        # Pattern for FROM clause
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
        matches = re.findall(from_pattern, sql, re.IGNORECASE)
        tables.update(matches)
        
        # Pattern for JOIN clauses
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        tables.update(matches)
        
        return list(tables)
    
    def _extract_columns(self, sql: str) -> List[str]:
        """Extract column references"""
        columns = set()
        
        # Remove string literals to avoid false positives
        sql_no_strings = re.sub(r"'[^']*'", '', sql)
        
        # Pattern for table.column or just column references
        # Exclude SQL keywords and functions
        column_pattern = r'(?:^|[^a-zA-Z_])([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:[,\s\)]|$)'
        
        for match in re.finditer(column_pattern, sql_no_strings):
            potential_col = match.group(2)
            # Filter out SQL keywords and common functions
            if potential_col.upper() not in ['SELECT', 'FROM', 'WHERE', 'AS', 'AND', 'OR', 
                                            'IF', 'THEN', 'ELSE', 'WHEN', 'CASE', 'END',
                                            'GROUP', 'ORDER', 'BY', 'HAVING', 'JOIN', 'ON']:
                if match.group(1):  # Has table prefix
                    columns.add(f"{match.group(1)}{potential_col}")
                else:
                    columns.add(potential_col)
        
        return list(columns)
    
    def _extract_functions(self, sql: str) -> List[str]:
        """Extract SQL functions used"""
        functions = set()
        
        # Pattern for function calls (word followed by parenthesis)
        func_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        for match in re.finditer(func_pattern, sql, re.IGNORECASE):
            func_name = match.group(1).upper()
            if func_name in self.sql_functions:
                functions.add(func_name)
        
        return list(functions)
    
    def _generate_description(self, sql: str) -> str:
        """Generate a succinct description of the query"""
        description_parts = []
        
        # Check for SELECT
        if 'SELECT' in sql.upper():
            # Check for conditional logic
            if any(word in sql.upper() for word in ['IF', 'CASE', 'WHEN']):
                description_parts.append("Conditional selection")
            
            # Check for date operations
            if 'TO_DATE' in sql.upper() or 'DATE' in sql.upper():
                description_parts.append("with date transformation")
            
            # Check for specific patterns
            if 'NewLookupRow' in sql and '1900-01-01' in sql:
                description_parts.append("setting default date for new lookup rows")
            
            # Check for aliasing
            if ' AS ' in sql.upper():
                alias_count = len(re.findall(r'\s+AS\s+', sql, re.IGNORECASE))
                description_parts.append(f"creating {alias_count} aliased column(s)")
        
        # Check for filtering
        if 'WHERE' in sql.upper():
            description_parts.append("with filtering")
        
        # Check for joins
        if 'JOIN' in sql.upper():
            description_parts.append("joining tables")
        
        # Check for aggregation
        if any(word in sql.upper() for word in ['GROUP BY', 'SUM', 'COUNT', 'AVG']):
            description_parts.append("with aggregation")
        
        if description_parts:
            return "Query performs: " + ", ".join(description_parts)
        else:
            return "Basic SELECT query"

def format_for_llm(parsed_info: Dict, original_sql: str) -> str:
    """Format parsed information for LLM consumption"""
    
    prompt = f"""Analyze and correct this BladeBridge-converted Spark SQL:

ORIGINAL SQL:
{original_sql}

EXTRACTED COMPONENTS:
- Tables: {', '.join(parsed_info['tables']) if parsed_info['tables'] else 'None detected'}
- Columns: {', '.join(parsed_info['columns']) if parsed_info['columns'] else 'None detected'}  
- Functions Used: {', '.join(parsed_info['functions']) if parsed_info['functions'] else 'None detected'}
- Query Intent: {parsed_info['description']}

Please provide:
1. Corrected Spark SQL
2. List of issues fixed
3. Brief explanation of changes
"""
    
    return prompt

# Usage
parser = MinimalSQLParser()

# Your query
blade_bridge_sql = """
SELECT
IF(FIL_Remove_Dups.NewLookupRow = 1, to_date('1900-01-01', 'yyyy-MM-dd'),
FIL_Remove_Dups.ctl_from_ts) as ctl_from_ts_out,
FIL_Remove_Dups.source_record_id
FROM
FIL_Remove_Dups"""

# Parse the query
parsed = parser.parse_query(blade_bridge_sql)

print("Parsed Information:")
print(f"Tables: {parsed['tables']}")
print(f"Columns: {parsed['columns']}")
print(f"Functions: {parsed['functions']}")
print(f"Description: {parsed['description']}")

# Format for LLM
llm_prompt = format_for_llm(parsed, blade_bridge_sql)
print("\nLLM Prompt:")
print(llm_prompt)
