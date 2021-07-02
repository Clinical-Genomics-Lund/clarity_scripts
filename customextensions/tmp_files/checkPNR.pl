#!/usr/bin/perl

use Algorithm::LUHN qw/check_digit is_valid/; 
use REST::Client;
use JSON;
use Data::Dumper;
use MIME::Base64;
use XML::Simple;
use Getopt::Std;


my %opts;
getopts('l:p:u:',\%opts);




open($utfata,">/tmp/testet");
print $utfata "------------------------------------\n";
print $utfata Dumper(%opts);


my @errors;

my $headers = {
        Accept        => 'application/json',
	Authorization => 'Basic ' . encode_base64($opts{u}. ':' . $opts{p})
};

my $client = REST::Client->new();
#$client->setHost('localhost/');

$client->GET($opts{l}, $headers);
#$client->GET( $opts{l}, $headers );


#print $utfata $opts{l}."\n";
#print $client->responseCode();
#print $client->responseContent();

my $xml = XMLin( $client->responseContent() );

print $utfata Dumper( $xml );

print $utfata "------------------------------------\n";

foreach my $item (@{ $xml->{'input-output-map'} } ) {
#    print $utfata "$item: \n";
#    foreach my $iteminitem (keys %{$item->{'input'}}){
	print $utfata "$item->{'input'}->{'limsid'} - ";
	my $clientAnalyte = REST::Client->new();
	$clientAnalyte->GET($item->{'input'}->{'uri'}, $headers);	

	my $xmlAnalyte = XMLin( $clientAnalyte->responseContent() );

	print $utfata $xmlAnalyte->{'sample'}->{'uri'}." - ";

	my $clientSample = REST::Client->new();
	$clientSample->GET($xmlAnalyte->{'sample'}->{'uri'}, $headers);

	my $xmlSample = XMLin( $clientSample->responseContent() );
	

	my $pnr = $xmlSample->{'udf:field'}->{'Personal Identity Number'}->{'content'};

	print $utfata Dumper($xmlSample->{'udf:field'});
	$pnr =~ s/\D//g;
#	print $utfata $pnr;
	my $valid = is_valid($pnr);

	print $utfata "Fel personnumer \|". $valid ."\| $pnr --- ".(length($pnr)==10) ;#unless ($valid and length($pnr)==10);

	if( !$valid or length($pnr) != 10 ) {
 	    push(@errors,"Fel personnummer ".$xmlAnalyte->{'sample'}->{'uri'}." - $pnr");
	}

	print $utfata "\n";


#	print $utfata Dumper($xmlSample);


#	my $url = "http://localhost:9080/api/v2/samples".$item->{'input'}->{'limsid'};
#	print $utfata "$url\n";
#	$client2->GET($url, $headers);
#	my $sampleXML = XMLin( $client2->responseContent() );
	

}	

if (@errors){


    my $to = 'petter.storm@skane.se';
    my $from = 'petter.storm@skane.se';
    my $subject = 'Felaktiga personnummer';

    open(MAIL, "|/usr/sbin/sendmail -t");

    # Email Header
    print MAIL "To: $to\n";
    print MAIL "From: $from\n";
    print MAIL "Subject: $subject\n\n";
    # Email Body
    foreach(@errors){
	print MAIL "$_\n\n";
    }


    close(MAIL);
}
#print $utfata "\nhej baberiba".$xml->{'input-output-map'}->[0]->{'input'}->{'limsid'};



print "Looking good, ".$xml->{technician}->{'first-name'}."!";


exit 0;

#$client->PUT( $ARGV[0], '<udf:field type="String" name="Jobnummer">342341111111</udf:field>', $headers );
$client->PUT( $ARGV[0], '<working-flag>false</working-flag>', $headers );
print "\n\n";
print $client->responseCode();
print $client->responseContent();



open($utfata,">/tmp/testet");
foreach(@ARGV){print $utfata "$_\n";}
exit 0;
