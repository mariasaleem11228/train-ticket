package trainticket.contacts;

public record Contact(String id, String accountId, String name, int documentType,
                      String documentNumber, String phoneNumber) { }
