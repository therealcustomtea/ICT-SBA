// Imports the promise-based file helpers used to read and replace the generated schema.
import { readFile, writeFile } from 'node:fs/promises';

// Resolves the generated schema relative to this script so the command works from any directory.
const schemaUrl = new URL('../src/schema.ts', import.meta.url);
// Identifies comments emitted by this script so a repeated run does not duplicate them.
const annotationPrefix = '// Generated declaration:';

// Returns the property name at the start of a generated TypeScript member when one is present.
const propertyName = (line) => {
  // Matches quoted OpenAPI paths as well as ordinary TypeScript property identifiers.
  const match = line.match(/^(?:readonly\s+)?(?:['"]([^'"]+)['"]|([A-Za-z_$][\w$]*))\??\s*:/);
  // Returns the captured path or identifier, or null when the line is not a property.
  return match?.[1] ?? match?.[2] ?? null;
  // Closes the property-name helper.
};

// Builds a concise explanation for one generated TypeScript declaration line.
const explainLine = (line) => {
  // Detects exported interfaces and names the contract section they expose.
  const interfaceMatch = line.match(/^export interface ([A-Za-z_$][\w$]*)/);
  // Returns an interface-specific explanation when the declaration matched.
  if (interfaceMatch) {
    // Explains that consumers use this generated interface as part of the API contract.
    return `exports the ${interfaceMatch[1]} interface for consumers of the OpenAPI contract.`;
    // Closes the interface-specific branch.
  }

  // Detects exported type aliases and names the generated type they expose.
  const typeMatch = line.match(/^export type ([A-Za-z_$][\w$]*)/);
  // Returns a type-specific explanation when the declaration matched.
  if (typeMatch) {
    // Explains that consumers use this alias as part of the generated API contract.
    return `exports the ${typeMatch[1]} type alias for consumers of the OpenAPI contract.`;
    // Closes the type-alias branch.
  }

  // Extracts a generated member name when the line begins with a property declaration.
  const member = propertyName(line);
  // Gives generated properties a useful name-based explanation.
  if (member) {
    // Distinguishes nested objects from scalar, reference, or union-valued members.
    const action = line.endsWith('{') ? 'opens the object for' : 'defines the generated type of';
    // Returns the property explanation used immediately above the generated member.
    return `${action} the ${member} property.`;
    // Closes the generated-property branch.
  }

  // Identifies closing delimiters emitted for interfaces, objects, and nested declarations.
  if (/^[}\]];?,?$/.test(line)) {
    // Explains that this delimiter completes a surrounding generated construct.
    return 'closes the generated declaration opened above.';
    // Closes the delimiter branch.
  }

  // Identifies additional alternatives in multiline generated union types.
  if (line.startsWith('|')) {
    // Explains how this line contributes to the surrounding generated union.
    return 'adds another allowed type to the surrounding union.';
    // Closes the union-alternative branch.
  }

  // Identifies generated index signatures used for status codes and media types.
  if (line.startsWith('[')) {
    // Explains that the signature maps a generated key to its declared value type.
    return 'defines an index signature for generated OpenAPI keys and values.';
    // Closes the index-signature branch.
  }

  // Provides a safe explanation for uncommon generator output not covered above.
  return 'continues the generated OpenAPI type declaration.';
  // Closes the line-explanation helper.
};

// Reads the freshly generated TypeScript schema as UTF-8 text.
const source = await readFile(schemaUrl, 'utf8');
// Removes annotations from a previous direct script run while preserving generator comments.
const sourceLines = source
  // Splits the schema so each generated line can receive its own adjacent explanation.
  .split('\n')
  // Excludes only comments carrying this script's distinctive annotation prefix.
  .filter((line) => !line.trimStart().startsWith(annotationPrefix));
// Collects the original schema lines and the explanatory comments inserted before them.
const annotatedLines = [];
// Tracks whether iteration is currently inside a multiline comment emitted by the generator.
let insideBlockComment = false;

// Visits every generated line in its original order.
for (const line of sourceLines) {
  // Removes surrounding whitespace for syntax classification without changing saved indentation.
  const trimmed = line.trim();
  // Records whether this line begins a multiline generator comment.
  const startsBlockComment = trimmed.startsWith('/*');
  // Treats blank lines and existing comments as already self-documenting content.
  const isExistingComment =
    // Keeps every line within an existing multiline comment unchanged.
    insideBlockComment ||
    // Preserves the opening line of a generator-provided block comment.
    startsBlockComment ||
    // Preserves generator-provided single-line comments.
    trimmed.startsWith('//') ||
    // Preserves conventional interior lines of generator documentation blocks.
    trimmed.startsWith('*') ||
    // Preserves an explicit block-comment terminator when it appears independently.
    trimmed.startsWith('*/');

  // Adds an explanatory comment immediately before each nonblank generated code line.
  if (trimmed && !isExistingComment) {
    // Preserves the generated line's indentation so Prettier keeps the comment adjacent.
    const indentation = line.slice(0, line.length - line.trimStart().length);
    // Inserts the stable annotation prefix and a syntax-aware explanation of the next line.
    annotatedLines.push(`${indentation}${annotationPrefix} ${explainLine(trimmed)}`);
    // Closes the annotation-insertion branch.
  }

  // Preserves the original generated line after any adjacent explanatory comment.
  annotatedLines.push(line);

  // Enters multiline-comment mode only when the comment does not also end on this line.
  if (startsBlockComment && !trimmed.includes('*/')) {
    // Prevents annotations from being inserted inside generated documentation comments.
    insideBlockComment = true;
    // Closes the multiline-comment entry branch.
  }
  // Leaves multiline-comment mode after the generator's closing marker is encountered.
  if (insideBlockComment && trimmed.includes('*/')) {
    // Allows the next generated code line to receive its explanatory annotation.
    insideBlockComment = false;
    // Closes the multiline-comment exit branch.
  }
  // Closes the loop after every generated schema line has been processed.
}

// Replaces the generated schema with the reproducibly annotated version.
await writeFile(schemaUrl, annotatedLines.join('\n'), 'utf8');
