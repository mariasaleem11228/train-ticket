package trainticket.rebook;

public interface RebookOperations {
    RebookResult<?> rebook(RebookInfo info);
    RebookResult<?> payDifference(RebookInfo info);
}
