//
//  ViewController.m
//  package
//
//  Created by lq on 2021/6/22.
//  test

#import "ViewController.h"

@interface ViewController ()

@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    
    UILabel *lqLb = [[UILabel alloc] initWithFrame:CGRectMake(100, 100, 100, 100)];
    lqLb.text = @"liqiang";
    [self.view addSubview:lqLb];
    
    // Do any additional setup after loading the view.
}


@end
