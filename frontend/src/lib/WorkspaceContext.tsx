import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getPlants } from "./api";

interface WorkspaceContextType {
  plantId: string;
  setPlantId: (id: string) => void;
  plants: string[];
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  plantId: "DEMO-PLANT",
  setPlantId: () => {},
  plants: [],
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [plantId, setPlantId] = useState("DEMO-PLANT");
  const [plants, setPlants] = useState<string[]>(["DEMO-PLANT"]);

  useEffect(() => {
    getPlants()
      .then((data) => {
        const ids = data.map((p: any) => p.plant_id);
        if (ids.length > 0) {
          setPlants(ids);
          // Auto-select first plant if current not in list
          if (!ids.includes(plantId)) {
            setPlantId(ids[0]);
          }
        }
      })
      .catch(() => {});
  }, []);

  return (
    <WorkspaceContext.Provider value={{ plantId, setPlantId, plants }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
