import { ConceptMasteryRead } from "@/lib/types";

export function getWeakConcepts(masteries: ConceptMasteryRead[]) {
  return masteries.filter((mastery) => mastery.is_weak);
}

export function groupMasteryByLecture(masteries: ConceptMasteryRead[]) {
  return masteries.reduce<Record<string, ConceptMasteryRead[]>>((accumulator, mastery) => {
    accumulator[mastery.lecture_title] ||= [];
    accumulator[mastery.lecture_title].push(mastery);
    return accumulator;
  }, {});
}
