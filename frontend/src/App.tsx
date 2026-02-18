import React, { useState, useCallback } from "react";
import { Toolbar } from "@/components/Layout/Toolbar";
import { Sidebar } from "@/components/Layout/Sidebar";
import { SplitPane } from "@/components/Layout/SplitPane";
import { PromptInput } from "@/components/Prompt/PromptInput";
import { AIExplanation } from "@/components/Prompt/AIExplanation";
import { DiagramCanvas } from "@/components/Canvas/DiagramCanvas";
import { CodeEditor } from "@/components/Editor/CodeEditor";
import { ErrorMarker } from "@/components/Editor/ErrorMarker";
import { useDiagramStore } from "@/stores/diagramStore";
import { useCodeStore } from "@/stores/codeStore";
import { useSessionStore } from "@/stores/sessionStore";
import { useBidirectionalSync } from "@/hooks/useBidirectionalSync";
import { apiClient } from "@/services/apiClient";
import { parseDiagramCode } from "@/services/codeParser";
import type { PromptResponse } from "@/types/api";

const App: React.FC = () => {
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiAssumptions, setAiAssumptions] = useState<string[]>([]);
  const [aiWarnings, setAiWarnings] = useState<string[]>([]);
  const [aiModel, setAiModel] = useState("");

  const setGraphModel = useDiagramStore((s) => s.setGraphModel);
  const setSourceCode = useCodeStore((s) => s.setSourceCode);
  const { isLoading, setLoading, setDiagramId } = useSessionStore();
  const { handleCodeChange } = useBidirectionalSync();

  const handlePromptSubmit = useCallback(
    async (prompt: string) => {
      setLoading(true);
      try {
        const response: PromptResponse = await apiClient.generateFromPrompt({
          prompt,
        });

        // Update code store
        setSourceCode(response.diagram.source_code || "");

        // Update diagram ID
        setDiagramId(response.diagram.id);

        // Update AI explanation
        setAiExplanation(response.explanation);
        setAiAssumptions(response.assumptions);
        setAiWarnings(response.warnings);
        setAiModel(response.model_used);

        // Use server-provided graph model (has accurate icon paths from registry)
        const graphModel = (response.diagram as any).graph_model;
        if (graphModel && graphModel.nodes && graphModel.nodes.length > 0) {
          setGraphModel(graphModel);
        } else {
          // Fallback to client-side parser
          const model = parseDiagramCode(response.diagram.source_code || "");
          setGraphModel(model);
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to generate diagram";
        setAiWarnings([message]);
      } finally {
        setLoading(false);
      }
    },
    [setGraphModel, setSourceCode, setLoading, setDiagramId],
  );

  return (
    <div className="flex h-screen flex-col">
      <Toolbar />
      <main className="flex flex-1 overflow-hidden">
        <Sidebar>
          <PromptInput onSubmit={handlePromptSubmit} isLoading={isLoading} />
          <AIExplanation
            explanation={aiExplanation}
            assumptions={aiAssumptions}
            warnings={aiWarnings}
            modelUsed={aiModel}
          />
        </Sidebar>
        <SplitPane
          left={
            <div className="flex h-full flex-col">
              <CodeEditor onChange={handleCodeChange} />
              <ErrorMarker />
            </div>
          }
          right={<DiagramCanvas />}
        />
      </main>
    </div>
  );
};

export default App;
