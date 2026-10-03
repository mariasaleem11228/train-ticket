package trainticket.voucher;

record VoucherDetails(String id, String travelDate, String travelTime, String contactName,
                      String trainNumber, int seatClass, String seatNumber,
                      String startStation, String destStation, float price) { }
