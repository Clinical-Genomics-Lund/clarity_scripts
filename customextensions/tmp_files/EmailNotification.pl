#!/usr/bin/perl

use strict;
use Getopt::Std;
use File::Basename;

use POSIX qw(strftime);

my $date = strftime "%Y-%m-%d", localtime;
#print $date;

my %opts;
getopts('l:t:p:',\%opts);


my $to = 'petter.storm@skane.se';
my $from = 'petter.storm@skane.se';
my $subject = 'Test Email';

my $message=" $opts{l} $opts{p}" || 12;

open(MAIL, "|/usr/sbin/sendmail -t");

# Email Header
print MAIL "To: $to\n";
print MAIL "From: $from\n";
print MAIL "Subject: $subject\n\n";
# Email Body
print MAIL $message;

close(MAIL);
print "Email Sent Successfully\n";
