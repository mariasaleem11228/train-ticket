package trainticket;

import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.Test;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;

class ArchitectureTest {
    @Test void preserveUsesOnlyPublishedModuleApis() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.preserve..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.security.internal..", "trainticket.contacts.internal..",
                        "trainticket.travel.internal..", "trainticket.station.internal..",
                        "trainticket.seat.internal..", "trainticket.orders.internal..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.preserve..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.preserve.internal..")
                .check(classes);
    }
    @Test void contactsInternalsArePrivateAndApiIsPersistenceFree() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideOutsideOfPackage("trainticket.contacts..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.contacts.internal..")
                .check(classes);
        noClasses().that().resideInAPackage("trainticket.contacts").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.contacts.internal..")
                .check(classes);
    }
    @Test void travelPlanUsesPublishedModuleApis() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.travelplan..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.station.internal..", "trainticket.seat.internal..",
                        "trainticket.travel.internal..", "trainticket.travel2.internal..",
                        "trainticket.routeplan.internal..", "org.springframework.web.client..", "java.net..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.travelplan..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.travelplan.internal..")
                .check(classes);
    }
    @Test void routePlanUsesPublishedModuleApis() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.routeplan..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.station.internal..", "trainticket.route.internal..",
                        "trainticket.travel.internal..", "trainticket.travel2.internal..",
                        "org.springframework.web.client..", "java.net..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.routeplan..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.routeplan.internal..")
                .check(classes);
    }
    @Test void travel2UsesPublishedModuleApis() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.travel2..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.train.internal..", "trainticket.route.internal..",
                        "trainticket.orders.internal..", "trainticket.seat.internal..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.travel2..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.travel2.internal..")
                .check(classes);
    }
    @Test void travelUsesPublishedModuleApis() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.travel..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.train.internal..", "trainticket.route.internal..",
                        "trainticket.orders.internal..", "trainticket.seat.internal..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.travel..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.travel.internal..")
                .check(classes);
    }
    @Test void basicUsesOnlyPublishedCatalogueContracts() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket");
        noClasses().that().resideInAPackage("trainticket.basic..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "trainticket.station.internal..", "trainticket.train.internal..",
                        "trainticket.route.internal..", "trainticket.price.internal..",
                        "org.springframework.web.client..", "java.net..")
                .check(classes);
        noClasses().that().resideOutsideOfPackage("trainticket.basic..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.basic.internal..")
                .check(classes);
    }
    @Test void priceInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.price..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.price.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void priceApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.price").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.price.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void routeInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.route..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.route.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void routeApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.route").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.route.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void trainInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.train..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.train.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void trainApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.train").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.train.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void stationInternalsArePrivateToTheModule() {
        noClasses().that().resideOutsideOfPackage("trainticket.station..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.station.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void publicApiDoesNotExposePersistenceOrWebFramework() {
        noClasses().that().resideInAPackage("trainticket.station").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.station.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void moduleDependenciesHaveNoCycles() {
        slices().matching("trainticket.(*)..").should().beFreeOfCycles()
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void ordersInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.orders..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.orders.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void ordersApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.orders").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.orders.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void ordersDoesNotCallStationOverHttp() {
        noClasses().that().resideInAPackage("trainticket.orders..")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework.web.client..", "java.net..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void orderOtherUsesOnlyStationExportedApi() {
        noClasses().that().resideInAPackage("trainticket.orderother..")
                .should().dependOnClassesThat().resideInAnyPackage("trainticket.station.internal..", "org.springframework.web.client..", "java.net..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void orderOtherInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.orderother..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.orderother.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void orderOtherApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.orderother").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.orderother.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void configInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.config..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.config.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void configApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.config").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.config.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void seatInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.seat..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.seat.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void seatApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.seat").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.seat.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void securityInternalsArePrivate() {
        noClasses().that().resideOutsideOfPackage("trainticket.security..")
                .should().dependOnClassesThat().resideInAPackage("trainticket.security.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
    @Test void securityApiHasNoWebOrPersistenceDependencies() {
        noClasses().that().resideInAPackage("trainticket.security").and().doNotHaveSimpleName("package-info")
                .should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "com.mongodb..", "org.bson..", "trainticket.security.internal..")
                .check(new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("trainticket"));
    }
}
