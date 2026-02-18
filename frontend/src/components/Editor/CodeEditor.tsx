/**
 * CodeEditor — Monaco Editor with Python syntax highlighting and
 * onDidChangeModelContent callback for live preview.
 */

import React, { useCallback, useRef } from "react";
import Editor, { type OnMount, type OnChange } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { useCodeStore } from "@/stores/codeStore";

interface CodeEditorProps {
  onChange?: (value: string) => void;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  onChange,
  readOnly = false,
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const sourceCode = useCodeStore((s) => s.sourceCode);
  const errors = useCodeStore((s) => s.errors);
  const setSourceCode = useCodeStore((s) => s.setSourceCode);

  const handleMount: OnMount = useCallback(
    (editorInstance) => {
      editorRef.current = editorInstance;
    },
    [],
  );

  const handleChange: OnChange = useCallback(
    (value) => {
      const code = value || "";
      setSourceCode(code);
      onChange?.(code);
    },
    [setSourceCode, onChange],
  );

  // Apply error markers whenever errors change
  React.useEffect(() => {
    if (!editorRef.current) return;
    const model = editorRef.current.getModel();
    if (!model) return;

    const monaco = (window as any).monaco;
    if (!monaco) return;

    const markers = errors.map((err) => ({
      severity:
        err.severity === "error"
          ? monaco.MarkerSeverity.Error
          : monaco.MarkerSeverity.Warning,
      startLineNumber: err.line,
      startColumn: err.column || 1,
      endLineNumber: err.line,
      endColumn: err.column ? err.column + 10 : model.getLineMaxColumn(err.line),
      message: err.message,
    }));

    monaco.editor.setModelMarkers(model, "diagram-validation", markers);
  }, [errors]);

  return (
    <div className="h-full w-full">
      <Editor
        height="100%"
        language="python"
        theme="vs-light"
        value={sourceCode}
        onChange={handleChange}
        onMount={handleMount}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          wordWrap: "on",
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: true,
        }}
      />
    </div>
  );
};
